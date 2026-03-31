# Kubernetes Deployment Guide

---

## Overview

Kubernetes manifests are in `k8s/` using Kustomize overlays for environment-specific config.

```
k8s/
├── base/              # Gateway deployment, service, ingress, namespace
├── databases/         # StatefulSets and Deployments for each DB
├── autoscaling/       # HPA + KEDA scalers
├── observability/     # Prometheus, Grafana, Loki, Jaeger
├── security/          # NetworkPolicy + PodSecurity
└── overlays/
    ├── dev/           # Dev overlay (reduced resources)
    ├── prod/          # Production overlay (HA, rolling updates)
    └── enterprise/    # Enterprise overlay (full stack)
```

---

## Prerequisites

- Kubernetes 1.30+
- `kubectl` configured for your cluster
- `kustomize` v5+ (or `kubectl apply -k`)
- A container registry with built images

---

## Step 1 — Create Secrets

```bash
kubectl create namespace ascended

kubectl create secret generic ascended-secrets \
  --namespace=ascended \
  --from-literal=jwt-secret-key="$(openssl rand -hex 32)" \
  --from-literal=postgres-password="your-password" \
  --from-literal=admin-password="your-admin-password" \
  --from-literal=minio-secret-key="your-minio-secret"
```

---

## Step 2 — Deploy (Dev)

```bash
kubectl apply -k k8s/overlays/dev
```

This deploys: gateway + postgres + redis + minio in the `ascended` namespace.

---

## Step 3 — Deploy (Production)

```bash
kubectl apply -k k8s/overlays/prod
```

Adds: qdrant, ingress with TLS, HPA for gateway.

---

## Step 4 — Deploy (Enterprise)

```bash
kubectl apply -k k8s/overlays/enterprise
```

Adds: neo4j, clickhouse, kafka, KEDA scalers, full observability stack.

---

## Step 5 — Verify Pods

```bash
kubectl get pods -n ascended
kubectl get svc -n ascended
kubectl get ingress -n ascended
```

Expected output:
```
NAME                          READY   STATUS    RESTARTS   AGE
gateway-7d9b8f6c4-x2kpq       1/1     Running   0          2m
gateway-7d9b8f6c4-w9mnb       1/1     Running   0          2m
postgres-0                    1/1     Running   0          3m
redis-5f8b7c9d6-qrtlp         1/1     Running   0          3m
```

---

## Helm Alternative

Deploy using Helm charts:

```bash
# Install the full stack
helm install ascended ./helm/full-stack-chart \
  --namespace ascended \
  --create-namespace \
  --set global.environment=dev \
  --set postgres.password=changeme \
  --set jwt.secretKey=$(openssl rand -hex 32)

# Upgrade
helm upgrade ascended ./helm/full-stack-chart --namespace ascended

# Uninstall
helm uninstall ascended --namespace ascended
```

---

## Ingress

The ingress is configured for NGINX with TLS via cert-manager:

```yaml
# k8s/base/ingress.yaml
rules:
  - host: api.yourdomain.com
    http:
      paths:
        - path: /
          backend:
            service:
              name: gateway
              port:
                number: 8000
```

Update the hostname in `k8s/overlays/prod/kustomization.yaml` before deploying.

---

## Autoscaling

The gateway HPA scales between 2–10 replicas based on CPU:

```bash
kubectl get hpa -n ascended
# NAME          REFERENCE          TARGETS   MINPODS   MAXPODS   REPLICAS
# gateway-hpa   Deployment/gateway  45%/70%   2         10        3
```

KEDA Kafka scaler (enterprise):
```bash
kubectl get scaledobject -n ascended
```

---

## Monitoring

Port-forward Grafana:
```bash
kubectl port-forward -n ascended svc/grafana 3000:3000
```

Open: `http://localhost:3000` (default admin/admin — change immediately)
