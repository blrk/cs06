FROM openjdk:17-jdk-slim

ENV ELASTIC_VERSION=8.13.0

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg unzip && \
    rm -rf /var/lib/apt/lists/*

# Add Elasticsearch user
RUN useradd -ms /bin/bash elastic

# Download and extract Elasticsearch
RUN wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-${ELASTIC_VERSION}-linux-x86_64.tar.gz && \
    tar -xzf elasticsearch-${ELASTIC_VERSION}-linux-x86_64.tar.gz && \
    mv elasticsearch-${ELASTIC_VERSION} /opt/elasticsearch && \
    rm elasticsearch-${ELASTIC_VERSION}-linux-x86_64.tar.gz

# Copy configs
COPY elasticsearch.yml /opt/elasticsearch/config/elasticsearch.yml
COPY jvm.options /opt/elasticsearch/config/jvm.options
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Data and logs directories
RUN mkdir -p /opt/elasticsearch/data /opt/elasticsearch/logs && \
    chown -R elastic:elastic /opt/elasticsearch

USER elastic
WORKDIR /opt/elasticsearch
ENTRYPOINT ["entrypoint.sh"]

