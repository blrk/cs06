####
* Bring the cluster up 
```bash
docker-compose down && docker-compose up --build -d
```
### Stream app apis
```bash
docker inspect --format='{{json .State.Health}}' streamapp | jq
```
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

### Elastic search queries 
```bash
curl -X GET "http://localhost:9200/log-anomalies/_search?pretty&size=100&sort=event_timestamp:desc" | jq
```
```bash
curl -X GET "http://localhost:9200/log-anomalies/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "size": 100,
  "sort": [{"event_timestamp": "desc"}],
  "script_fields": {
    "timestamp_as_date": {
      "script": {
        "source": "Instant.ofEpochMilli(doc['event_timestamp'].value).atZone(ZoneId.of('UTC')).format(DateTimeFormatter.ISO_DATE_TIME)",
        "lang": "painless"
      }
    }
  }
}'
```

#### Download
```bash
 downloading https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.0/spark-sql-kafka-0-10_2.12-3.4.0.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] org.apache.spark#spark-sql-kafka-0-10_2.12;3.4.0!spark-sql-kafka-0-10_2.12.jar (1068ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/elasticsearch/elasticsearch-spark-30_2.12/8.18.3/elasticsearch-spark-30_2.12-8.18.3.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] org.elasticsearch#elasticsearch-spark-30_2.12;8.18.3!elasticsearch-spark-30_2.12.jar (2173ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.4.0/spark-token-provider-kafka-0-10_2.12-3.4.0.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] org.apache.spark#spark-token-provider-kafka-0-10_2.12;3.4.0!spark-token-provider-kafka-0-10_2.12.jar (2439ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.3.2/kafka-clients-3.3.2.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] org.apache.kafka#kafka-clients;3.3.2!kafka-clients.jar (13420ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/com/google/code/findbugs/jsr305/3.0.0/jsr305-3.0.0.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] com.google.code.findbugs#jsr305;3.0.0!jsr305.jar (1154ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] org.apache.commons#commons-pool2;2.11.1!commons-pool2.jar (3736ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-client-runtime/3.3.4/hadoop-client-runtime-3.3.4.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] org.apache.hadoop#hadoop-client-runtime;3.3.4!hadoop-client-runtime.jar (19098ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/lz4/lz4-java/1.8.0/lz4-java-1.8.0.jar ...
^F^Fkafaka-consumer  | 	[SUCCESSFUL ] org.lz4#lz4-java;1.8.0!lz4-java.jar (202915ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/xerial/snappy/snappy-java/1.1.9.1/snappy-java-1.1.9.1.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] org.xerial.snappy#snappy-java;1.1.9.1!snappy-java.jar(bundle) (17635ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/slf4j/slf4j-api/2.0.6/slf4j-api-2.0.6.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] org.slf4j#slf4j-api;2.0.6!slf4j-api.jar (412ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-client-api/3.3.4/hadoop-client-api-3.3.4.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] org.apache.hadoop#hadoop-client-api;3.3.4!hadoop-client-api.jar (6866ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/commons-logging/commons-logging/1.1.3/commons-logging-1.1.3.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] commons-logging#commons-logging;1.1.3!commons-logging.jar (18551ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/scala-lang/scala-reflect/2.12.19/scala-reflect-2.12.19.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] org.scala-lang#scala-reflect;2.12.19!scala-reflect.jar (2686ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/javax/xml/bind/jaxb-api/2.3.1/jaxb-api-2.3.1.jar ...
kafaka-consumer  | 	[SUCCESSFUL ] javax.xml.bind#jaxb-api;2.3.1!jaxb-api.jar (38115ms)
kafaka-consumer  | downloading https://repo1.maven.org/maven2/org/apache/spark/spark-yarn_2.12/3.4.3/spark-yarn_2.12-3.4.3.jar ...
```
