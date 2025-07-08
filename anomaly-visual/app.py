from flask import Flask, render_template
from elasticsearch import Elasticsearch
import pandas as pd
import plotly.express as px
import time
from datetime import datetime, timedelta

app = Flask(__name__)

# Elasticsearch configuration
ES_HOST = "http://elasticsearch:9200"
INDEX_NAME = "log-anomalies"

def get_anomaly_data(minutes=15):
    """Fetch anomalies from Elasticsearch"""
    es = Elasticsearch(ES_HOST)
    
    # Calculate time range
    time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
    
    # Elasticsearch query
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"anomaly": 1.0}},
                    {"range": {
                        "event_timestamp": {
                            "gte": time_threshold.isoformat(),
                            "lte": "now"
                        }
                    }}
                ]
            }
        },
        "sort": [{"event_timestamp": {"order": "desc"}}],
        "size": 1000
    }
    
    response = es.search(index=INDEX_NAME, body=query)
    hits = response['hits']['hits']
    return [hit['_source'] for hit in hits]

def create_visualizations(data):
    """Create Plotly visualizations"""
    df = pd.DataFrame(data)
    
    if df.empty:
        return None, None
    
    # Convert timestamp from milliseconds to datetime
    df['timestamp'] = pd.to_datetime(df['event_timestamp'], unit='ms')
    
    # Time series visualization
    time_series = px.scatter(
        df,
        x='timestamp',
        y='anomaly_score',
        color='anomaly_score',
        title='Anomaly Scores Over Time',
        labels={'anomaly_score': 'Anomaly Score', 'timestamp': 'Time'},
        hover_data=['message']
    )
    time_series.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')))
    
    # Top messages visualization
    top_messages = df.nlargest(10, 'anomaly_score')
    messages_fig = px.bar(
        top_messages,
        x='anomaly_score',
        y='message',
        orientation='h',
        title='Top Anomalous Messages',
        hover_data=['timestamp'],
        text='anomaly_score'
    )
    messages_fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    messages_fig.update_layout(yaxis={'categoryorder':'total ascending'})
    
    return time_series.to_json(), messages_fig.to_json()

@app.route('/')
def dashboard():
    data = get_anomaly_data()
    time_series_json, messages_json = create_visualizations(data)
    
    return render_template(
        'index.html',
        time_series=time_series_json,
        messages_chart=messages_json,
        anomaly_count=len(data),
        last_update=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=True)