# File: big/streamapp/main.py

from flask import Flask, request, jsonify
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import os
import time

producer = None
admin_client = None

def create_app():
    global producer, admin_client

    app = Flask(__name__)
    app.logger.setLevel("DEBUG")

    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    # --- Initialize Kafka Admin ---
    for i in range(10):
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
            print(f"[✔] Kafka Admin connected at {KAFKA_BOOTSTRAP_SERVERS}")
            break
        except Exception as e:
            print(f"[⏳] Kafka Admin not available (attempt {i+1}/10)... retrying")
            time.sleep(2)
    else:
        raise Exception("[✘] Kafka Admin not available after 10 attempts")

    # --- Initialize Kafka Producer ---
    for i in range(10):
        try:
            producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
            print(f"[✔] Kafka Producer connected at {KAFKA_BOOTSTRAP_SERVERS}")
            break
        except Exception as e:
            print(f"[⏳] Kafka Producer not available (attempt {i+1}/10)... retrying")
            time.sleep(2)
    else:
        raise Exception("[✘] Kafka Producer not available after 10 attempts")

    @app.route("/upload/<topic>", methods=["POST"])
    def upload_file(topic):
        global producer, admin_client

        existing_topics = admin_client.list_topics()
        if topic not in existing_topics:
            try:
                new_topic = NewTopic(name=topic, num_partitions=1, replication_factor=1)
                admin_client.create_topics([new_topic])
                print(f"[✔] Created new topic: {topic}")
            except TopicAlreadyExistsError:
                print(f"[ℹ️] Topic '{topic}' already exists")
            except Exception as e:
                return jsonify({"error": f"Failed to create topic: {str(e)}"}), 500

        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        for line in file:
            line = line.decode("utf-8").strip()
            if line:
                producer.send(topic, value=line.encode("utf-8"))
                print(f"[→ {topic}] {line}")

        return jsonify({"message": f"File streamed to topic '{topic}'"}), 200

    @app.route("/topics", methods=["GET"])
    def list_topics():
        global admin_client
        try:
            topics = sorted(admin_client.list_topics())
            return jsonify({"topics": topics})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/health", methods=["GET"])
    def health():
        return "OK", 200

    return app
