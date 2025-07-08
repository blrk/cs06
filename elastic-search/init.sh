#!/bin/bash

# Wait for Elasticsearch to be healthy
echo "Waiting for Elasticsearch to be ready..."
until curl -s http://localhost:9200/_cluster/health?wait_for_status=yellow | grep -q '"status":"yellow"'; do
  echo "Elasticsearch is not ready yet. Waiting..."
  sleep 5
done
echo "Elasticsearch is ready."

# Check if the index exists
if ! curl -s --head http://localhost:9200/log-anomalies | grep "200 OK"; then
  echo "Index 'log-anomalies' does not exist. Creating with correct mapping..."
  curl -X PUT "http://localhost:9200/log-anomalies?pretty" -H 'Content-Type: application/json' -d'
  {
    "mappings": {
      "properties": {
        "anomaly": {
          "type": "float"
        },
        "anomaly_score": {
          "type": "float"
        },
        "event_timestamp": {
          "type": "date",
          "format": "epoch_millis"
        },
        "log_line": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above" : 256
            }
          }
        },
        "message": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above" : 256
            }
          }
        }
      }
    }
  }
  '
  echo "Index 'log-anomalies' created with mapping."
else
  echo "Index 'log-anomalies' already exists. Skipping creation."
fi