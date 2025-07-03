from flask import Flask, request, jsonify
from kafka import KafkaProducer
import os

producer = None

def create_app():
    global producer

    app = Flask(__name__)
    app.logger.setLevel("DEBUG")
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic_name = os.getenv("KAFKA_TOPIC", "logs")

    # Connect to Kafka
    for i in range(10):
        try:
            producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers)
            print(f"[✔] Kafka connected at {kafka_bootstrap_servers}")
            break
        except Exception as e:
            print(f"[⏳] Kafka not available (attempt {i+1}/10)... retrying")
            import time
            time.sleep(2)
    else:
        raise Exception("[✘] Kafka not available after 10 attempts")

    @app.route("/upload", methods=["POST"])
    def upload_file():
        global producer
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        for line in file:
            line = line.decode("utf-8").strip()
            if line:
                producer.send(topic_name, value=line.encode("utf-8"))
                print(f"[Sent] {line}")

        return jsonify({"message": "File streamed to Kafka"})

    return app

    

    