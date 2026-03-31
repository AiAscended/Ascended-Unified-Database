# Observability Overview

The full observability stack provides four pillars of production visibility.

## Four Pillars

| Pillar | Tool | Purpose | Port |
|--------|------|---------|------|
| Metrics | Prometheus | Time-series metrics collection | 9090 |
| Dashboards | Grafana | Visualization and alerting | 3000 |
| Logs | Loki | Log aggregation and search | 3100 |
| Traces | Jaeger | Distributed request tracing | 16686 |

---

## Quick Access (Kubernetes port-forward)

```bash
# Prometheus
kubectl port-forward -n ascended svc/prometheus 9090:9090
# → http://localhost:9090

# Grafana (admin/admin — change on first login)
kubectl port-forward -n ascended svc/grafana 3000:3000
# → http://localhost:3000

# Jaeger UI
kubectl port-forward -n ascended svc/jaeger 16686:16686
# → http://localhost:16686
```

---

## Gateway Instrumentation

The gateway exposes three built-in observability endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness — returns `{"status":"ok"}` |
| `GET /ready` | Readiness — checks all configured DB connections |
| `GET /metrics` | Prometheus text-format metrics |

Key metrics exposed:

| Metric | Type | Description |
|--------|------|-------------|
| `gateway_requests_total` | Counter | Total requests by operation and status |
| `gateway_request_duration_seconds` | Histogram | Request latency by operation |
| `gateway_db_pool_size` | Gauge | Active DB connection pool size |
| `gateway_provider_errors_total` | Counter | Provider-level errors by DB type |

---

## Prometheus Scrape Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ascended-gateway'
    static_configs:
      - targets: ['gateway:8000']
    metrics_path: /metrics

  - job_name: 'ascended-admin'
    static_configs:
      - targets: ['admin-backend:8001']
    metrics_path: /admin/api/metrics/prometheus
    bearer_token_file: /etc/prometheus/token
```

---

## Log Aggregation

All services write structured JSON logs to stdout. Loki collects them via Promtail.

Query in Grafana Explore:
```logql
{namespace="ascended"} |= "error"
{namespace="ascended", container="gateway"} | json | operation="vector_search"
```

---

## Distributed Tracing

The gateway has OpenTelemetry instrumentation that automatically traces every request through to database calls.

In Jaeger UI:
1. Select service: `ascended-gateway`
2. Search by operation: `gateway_query`
3. Inspect trace to see DB call breakdown and latency

---

## Alerting (Grafana)

Pre-configured alert rules are in `k8s/observability/prometheus.yaml`:

| Alert | Threshold | Severity |
|-------|-----------|----------|
| GatewayHighErrorRate | >5% errors over 5m | warning |
| GatewayDown | No scrape for 2m | critical |
| PostgresConnectionSaturation | Pool > 90% | warning |
| RedisMemoryHigh | Memory > 80% | warning |
