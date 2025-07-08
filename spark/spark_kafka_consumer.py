import os
import time
import re
import joblib
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, regexp_extract, col, to_timestamp, date_format, trim, unix_timestamp
from pyspark.sql.types import StringType, StructType, StructField, DoubleType
import pandas as pd
import numpy as np
from datetime import datetime
import nltk
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords

# --------------------------
# Configurations
# --------------------------
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_NAME = "apache-log"
MODEL_PATH = "/opt/bitnami/spark/app/isolation_forest_model.pkl"
VECTORIZER_PATH = "/opt/bitnami/spark/app/count_vectorizer.pkl"
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200")
ELASTIC_INDEX = "log-anomalies"

# --------------------------
# Load model and vectorizer
# --------------------------
loaded_model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

# --------------------------
# Preprocess & Predict
# --------------------------
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def predict_anomaly_struct(log_line):
    try:
        clean = preprocess_text(log_line)
        vec = vectorizer.transform([clean]).toarray()
        score = loaded_model.decision_function(vec)[0]  # Score
        label = loaded_model.predict(vec)[0]            # 0 (normal), 1 (anomaly)
        return (float(label), float(score))
    except Exception as e:
        return (-99.0, -999.0)  # Fallback values for failures

# --------------------------
# Register UDF with StructType
# --------------------------

schema = StructType([
    StructField("anomaly", DoubleType(), True),
    StructField("anomaly_score", DoubleType(), True)
])

predict_anomaly = udf(predict_anomaly_struct, schema)

# --------------------------
# Start Spark session
# --------------------------
spark = SparkSession.builder \
    .appName("KafkaSparkAnomalyDetection") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.elasticsearch:elasticsearch-spark-30_2.12:8.18.3") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .getOrCreate()

# --------------------------
# Read from Kafka
# --------------------------
df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", TOPIC_NAME)
    .option("startingOffsets", "earliest")  
    .load()
)

df_parsed = df.selectExpr("CAST(value AS STRING) as log_line")

# Pattern to extract timestamp
timestamp_pattern = r"\[([A-Za-z]{3} [A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2} \d{4})\]"
# Pattern to extract the rest of the log after the timestamp
message_pattern = r"\[[A-Za-z]{3} [A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2} \d{4}\]\s*(.*)"
# Apply regexp_extract
df_extracted = df_parsed \
    .withColumn("timestamp_str", regexp_extract(col("log_line"), timestamp_pattern, 1)) \
    .withColumn("message", regexp_extract(col("log_line"), message_pattern, 1))
# Date format
apache_date_format = "EEE MMM dd HH:mm:ss yyyy"
#Convert the extracted string to a timestamp
#df_extracted = df_extracted.withColumn(
#    "event_timestamp", to_timestamp(col("timestamp"), to_timestamp(trim(col("timestamp_str")), apache_date_format)
#).drop("timestamp") # Drop the temporary string column
spark.conf.set("spark.sql.legacy.timeParserPolicy", "LEGACY")

#df_with_timestamp_and_message = df_extracted.withColumn(
#    "event_timestamp", to_timestamp(trim(col("timestamp_str")), apache_date_format)
#).drop("timestamp_str")
df_with_timestamp_and_message = df_extracted.withColumn(
    "event_timestamp", 
    to_timestamp(trim(col("timestamp_str")), apache_date_format)
).drop("timestamp_str")

#df_extracted = df_extracted.withColumn( "timestamp_parsed", to_timestamp("timestamp", "EEE MMM dd HH:mm:ss yyyy") )
#df_extracted = df_extracted.drop("timestamp")
#print("Time stamp caste and removed")
#df_extracted.columns
# Show results
#df_extracted.select("timestamp", "message").show(truncate=False)

#df_with_pred = df_extracted.withColumn("prediction", predict_anomaly("message"))
df_with_pred = df_with_timestamp_and_message.withColumn("prediction", predict_anomaly("message"))

# --------------------------
# Flatten struct fields
# --------------------------
df_final = df_with_pred.select(
    "event_timestamp",          # The parsed timestamp (TimestampType)
    "message",                  # The extracted log message text
    "prediction.anomaly",       # The anomaly label from the prediction struct
    "prediction.anomaly_score"  # The anomaly score from the prediction struct
)

#df_final = df_with_pred.select(
#    "message",
#    "prediction.anomaly",
#    "prediction.anomaly_score"
#)
# df_final = df_final.withColumn("timestamp", df_extracted["timestamp"])
# Add this before writing to Elasticsearch
df_final = df_final.withColumn(
    "event_timestamp", 
    col("event_timestamp").cast("timestamp")  # Ensure it's a timestamp type
)
# Then add explicit mapping for Elasticsearch
es_write_conf = {
    "es.mapping.timestamp": "event_timestamp",
    "es.mapping.date.format": "strict_date_optional_time||epoch_millis"
}

# --------------------------
# Write to Elasticsearch
# --------------------------
query = (
    df_final.writeStream
    .outputMode("append")
    .format("org.elasticsearch.spark.sql")
    .option("checkpointLocation", "/tmp/checkpoints/es")
    .option("es.nodes", ELASTICSEARCH_HOST.replace("http://", "").replace("https://", ""))
    .option("es.port", "9200")
    .option("es.resource", ELASTIC_INDEX)
    .option("es.mapping.date.rich", "false")  # Important for proper date handling
    .start()
)

#query = (
#    df_final.writeStream 
#    .outputMode("append")
#    .format("console")
#    .option("truncate", "false")
#    .start()
#)

query.awaitTermination()