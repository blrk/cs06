import os
import time
import re
import joblib
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType, StructType, StructField, DoubleType

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
from pyspark.sql.types import StructType, StructField

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
    .option("startingOffsets", "earliest")    # <-- ADDED THE DOT HERE
    .load()
)

df_parsed = df.selectExpr("CAST(value AS STRING) as log_line")

# --------------------------
# Apply UDF to get predictions
# --------------------------
df_with_pred = df_parsed.withColumn("prediction", predict_anomaly("log_line"))

# --------------------------
# Flatten struct fields
# --------------------------
df_final = df_with_pred.select(
    "log_line",
    "prediction.anomaly",
    "prediction.anomaly_score"
)

# --------------------------
# Write to Elasticsearch
# --------------------------
query = (
    df_final.writeStream # Ensure writing df_final now
    .outputMode("append")
    .format("org.elasticsearch.spark.sql")
    .option("checkpointLocation", "/tmp/checkpoints/es")
    .option("es.nodes", ELASTICSEARCH_HOST.replace("http://", "").replace("https://", ""))
    .option("es.port", "9200")
    .option("es.resource", ELASTIC_INDEX) # <-- THIS IS THE CORRECT LINE: NO TRAILING SLASH OR /_doc
    .start()
)
#query = (
#    df_parsed.writeStream 
#    .outputMode("append")
#    .format("console")
#    .option("truncate", "false")
#    .start()
#)

query.awaitTermination()
