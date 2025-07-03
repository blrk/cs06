import os
import time
from kafka import KafkaAdminClient
from pyspark.sql import SparkSession

# Wait for at least one topic to be available in Kafka
def wait_for_kafka_topic(bootstrap_servers, timeout_sec=300):
    print("⏳ Waiting for any Kafka topic to be available...")
    start_time = time.time()

    while True:
        try:
            admin = KafkaAdminClient(bootstrap_servers=bootstrap_servers, client_id='spark-waiter')
            topics = admin.list_topics()
            if topics:
                print(f"✅ Found topic(s): {topics}")
                return topics[0]  # Use the first available topic
        except Exception as e:
            print(f"⚠️ Kafka not ready yet: {e}")

        if time.time() - start_time > timeout_sec:
            raise TimeoutError("⛔ Timed out waiting for Kafka topics.")
        
        time.sleep(5)

# Setup
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
topic = wait_for_kafka_topic(KAFKA_BOOTSTRAP_SERVERS)

# Start Spark session
spark = SparkSession.builder.appName("KafkaSparkConsumer").getOrCreate()

# Read from Kafka
df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", topic)
    .load()
)

# Decode and process
df_parsed = df.selectExpr("CAST(value AS STRING)")

# Write to console
query = (
    df_parsed.writeStream
    .outputMode("append")
    .format("console")
    .start()
)

query.awaitTermination()
