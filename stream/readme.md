#### Upload
```bash
curl -F 'file=@logs-data/Apache.log' http://localhost:5000/upload
```
bash```
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic logs \
  --from-beginning
```