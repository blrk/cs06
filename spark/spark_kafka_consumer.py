from pyspark.sql import SparkSession
from pyspark.sql.functions import expr

spark = SparkSession.builder \
    .appName("KafkaLogConsumer") \
    .getOrCreate()

# Replace with your Kafka broker name inside Docker network
kafka_bootstrap_servers = "kafka:9092"

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", "logs") \
    .option("startingOffsets", "latest") \
    .load()

# Convert value from binary to string
logs_df = df.selectExpr("CAST(value AS STRING) as log_line")

# Print to console (or write to DB or file)
query = logs_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()
