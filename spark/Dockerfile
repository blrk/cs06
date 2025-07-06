# Base Spark image
FROM bitnami/spark:3.4.0

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies 
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Set working directory
WORKDIR /opt/bitnami/spark/app

# Copy Kafka consumer script into the container
COPY spark_kafka_consumer.py .

# Copy the ML model 
COPY isolation_forest_model.pkl count_vectorizer.pkl

# Set environment variable for Spark app
ENV SPARK_APPLICATION_PYTHON_FILE=spark_kafka_consumer.py

# Default command to run the Spark Kafka consumer
CMD [ "/opt/bitnami/spark/bin/spark-submit", \
      "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0", \
      "/opt/bitnami/spark/app/spark_kafka_consumer.py" ]