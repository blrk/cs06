### Stream app apis
#### List Kafka topics
```bash
curl http://localhost:5000/topics
```
#### Health check stream app
```bash
curl http://localhost:5000/health
```
#### Stream a topic and file 
```bash
curl -F 'file=@logs-data/Apache.log' http://localhost:5000/upload/"apache-log"
{"message":"File streamed to topic 'apache-log'"}
```

### List the topics from the kafka cluster 
```bash
docker exec -it kafka-cluster bash

kafka-topics.sh --bootstrap-server localhost:9092 --list
```
```output
apache-log
```
