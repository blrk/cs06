import os
import time
import re
import joblib
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType, IntegerType

# --------------------------
# Configurations
# --------------------------
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_NAME = "apache-log"  # Static topic
MODEL_PATH = "/opt/bitnami/spark/app/isolation_forest_model.pkl"
VECTORIZER_PATH = "/opt/bitnami/spark/app/vectorizer.pkl"
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

def predict_anomaly_udf(text):
    try:
        clean = preprocess_text(text)
        vec = vectorizer.transform([clean]).toarray()
        pred = loaded_model.predict(vec)
        return int(pred[0])
    except Exception as e:
        return -99  # Use -99 for errors

# Register as UDF
predict_anomaly = udf(predict_anomaly_udf, IntegerType())

# --------------------------
# Start Spark session
# --------------------------
spark = SparkSession.builder \
    .appName("KafkaSparkAnomalyDetection") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .getOrCreate()

# --------------------------
# Read from Kafka topic
# --------------------------
df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", TOPIC_NAME)
    .option("startingOffsets", "earliest")
    .option("maxOffsetsPerTrigger", 5000)
    .load()
)

df_parsed = df.selectExpr("CAST(value AS STRING) as log_line")

# --------------------------
# Predict anomalies
# --------------------------
df_with_anomaly = df_parsed.withColumn("anomaly", predict_anomaly(df_parsed["log_line"]))

# --------------------------
# Write to Elasticsearch
# --------------------------
query = (
    df_with_anomaly.writeStream
    .outputMode("append")
    .format("org.elasticsearch.spark.sql")
    .option("checkpointLocation", "/tmp/checkpoints/es")
    .option("es.nodes", ELASTICSEARCH_HOST)
    .option("es.resource", f"{ELASTIC_INDEX}/_doc")
    .start()
)

query.awaitTermination()
