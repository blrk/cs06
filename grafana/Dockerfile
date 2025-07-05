FROM debian:bullseye-slim

ENV GRAFANA_VERSION=10.3.1
ENV GRAFANA_HOME=/usr/share/grafana

# Install required packages
RUN apt-get update && \
    apt-get install -y wget tar ca-certificates libfontconfig && \
    useradd --system --home ${GRAFANA_HOME} --shell /bin/false grafana

# Working directory for install steps
WORKDIR /tmp

# Download, extract and install Grafana
RUN wget https://dl.grafana.com/oss/release/grafana-${GRAFANA_VERSION}.linux-amd64.tar.gz && \
    tar -zxvf grafana-${GRAFANA_VERSION}.linux-amd64.tar.gz && \
    mv grafana-v${GRAFANA_VERSION} ${GRAFANA_HOME} && \
    rm grafana-${GRAFANA_VERSION}.linux-amd64.tar.gz

# Create data/log folders and fix permissions
RUN mkdir -p /var/lib/grafana /var/log/grafana && \
    chown -R grafana:grafana ${GRAFANA_HOME} /var/lib/grafana /var/log/grafana

# Switch to Grafana user
USER grafana
WORKDIR ${GRAFANA_HOME}
EXPOSE 3000

ENTRYPOINT ["./bin/grafana-server", "--homepath=/usr/share/grafana"]
