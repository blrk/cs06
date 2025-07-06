import os
import time
from kafka import KafkaAdminClient
from pyspark.sql import SparkSession

# Load model & vectorizer only once
loaded_model = joblib.load("isolation_forest_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")  

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_NAME = "apache-log"  # Update to your topic name

# Preprocess the log string from the stream 
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text)  # remove text in brackets
    text = re.sub(r'\W', ' ', text)  # remove non-alphanumeric characters
    text = re.sub(r'\s+', ' ', text)  # remove extra spaces
    return text

def predict_anomaly(new_texts):
    clean_texts = [preprocess_text(str(t)) for t in new_texts]
    X_new = vectorizer.transform(clean_texts).toarray()
    return loaded_model.predict(X_new)

# Wait for topic to be available
def wait_for_specific_topic(bootstrap_servers, target_topic, timeout_sec=300):
    print(f"⏳ Waiting for topic '{target_topic}' to be available...")
    start_time = time.time()
    while True:
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=bootstrap_servers,
                client_id='spark-topic-checker'
            )
            topics = admin.list_topics()
            if target_topic in topics:
                print(f"✅ Found Kafka topic: {target_topic}")
                return
            else:
                print(f"⏳ Topic '{target_topic}' not found yet...")
        except Exception as e:
            print(f"⚠️ Kafka not ready yet: {e}")
        
        if time.time() - start_time > timeout_sec:
            raise TimeoutError(f"⛔ Timed out waiting for topic: {target_topic}")
        time.sleep(5)

wait_for_specific_topic(KAFKA_BOOTSTRAP_SERVERS, TOPIC_NAME)

# Start Spark session
spark = SparkSession.builder \
    .appName("KafkaSparkConsumer") \
    .getOrCreate()

# Read from Kafka topic with trigger limit
df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", TOPIC_NAME)
    .option("startingOffsets", "earliest")              # Optional: read from beginning
    .option("maxOffsetsPerTrigger", 5000)               # Limit each batch to 5000 messages can be changed 
    .load()
)

# Decode Kafka message value (logs)
df_parsed = df.selectExpr("CAST(value AS STRING)")
clean_texts = [preprocess_text(str(t)) for t in new_texts] # call the pre proicess
# Transform using the existing vectorizer
X_new = vectorizer.transform(clean_texts).toarray()
return loaded_model.predict(X_new)


# Write logs to console
query = (
    df_parsed.writeStream
    .outputMode("append")
    .format("console")
    .start()
)

query.awaitTermination()
