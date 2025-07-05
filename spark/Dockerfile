# Base Spark image
FROM bitnami/spark:3.4.0
USER root

RUN apt-get update && apt-get install -y curl

USER spark

# Set working directory
WORKDIR /opt/bitnami/spark/app

# Copy Kafka consumer script into the container
COPY spark_kafka_consumer.py .

# Optional: Set environment variable for Spark app
ENV SPARK_APPLICATION_PYTHON_FILE=spark_kafka_consumer.py

# Default command can be overridden at runtime
CMD [ "/opt/bitnami/spark/bin/spark-submit", \
      "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0", \
      "/opt/bitnami/spark/app/spark_kafka_consumer.py" ]