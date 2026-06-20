# Observability

All services emit OpenTelemetry **traces, metrics and logs** over OTLP/gRPC to the
collector in this namespace (`OTEL_EXPORTER_OTLP_ENDPOINT` in each service ConfigMap).
LLM calls in `retrieval-service` are auto-instrumented by OpenLLMetry, so each Groq
request is its own span with model, token usage and latency.

## What's in here

- `collector-configmap.yaml` / `collector-deployment.yaml` / `collector-service.yaml`
  — the OpenTelemetry Collector. Receives OTLP and fans out:
  traces → Tempo, metrics → Prometheus (remote-write), logs → Loki.

## Backends (install separately via Helm)

The collector forwards to Tempo, Prometheus, Loki and Grafana, which are **not**
templated here — install them into the `rag-monitoring` namespace and make sure the
service DNS names in `collector-configmap.yaml` match your release names:

```sh
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm install tempo grafana/tempo -n rag-monitoring
helm install loki grafana/loki -n rag-monitoring
helm install prometheus prometheus-community/prometheus -n rag-monitoring \
  --set server.extraFlags='{web.enable-remote-write-receiver}'
helm install grafana grafana/grafana -n rag-monitoring
```

Then add Tempo / Prometheus / Loki as Grafana data sources.

## Apply

```sh
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/observability/
```

## Local development

`docker compose up -d otel-lgtm` runs the Collector + Prometheus + Tempo + Loki +
Grafana as a single container. Point services at `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`
and open Grafana at http://localhost:3000.
