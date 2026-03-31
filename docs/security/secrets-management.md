# Secrets Management

## Development

Use `.env` file (never commit it):

```bash
cp .env.example .env
# Edit .env — fill in real secrets
```

`.env` is in `.gitignore`. Confirm it stays there:
```bash
grep "\.env$" .gitignore
# → .env
```

---

## Kubernetes (Production / Enterprise)

Use Kubernetes Secrets — never put plaintext secrets in manifests or `values.yaml`:

```bash
# Create the master secrets bundle
kubectl create secret generic ascended-secrets \
  --namespace ascended \
  --from-literal=jwt-secret-key="$(openssl rand -hex 32)" \
  --from-literal=postgres-password="$(openssl rand -base64 24)" \
  --from-literal=redis-password="$(openssl rand -base64 24)" \
  --from-literal=admin-password="$(openssl rand -base64 24)" \
  --from-literal=minio-secret-key="$(openssl rand -base64 24)"
```

Reference from a Pod:
```yaml
env:
  - name: JWT_SECRET_KEY
    valueFrom:
      secretKeyRef:
        name: ascended-secrets
        key: jwt-secret-key
  - name: POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: ascended-secrets
        key: postgres-password
```

---

## Key Rotation

### JWT Secret Rotation

1. Generate a new key: `openssl rand -hex 32`
2. Update the Kubernetes Secret: `kubectl edit secret ascended-secrets -n ascended`
3. Restart the gateway: `kubectl rollout restart deployment/gateway -n ascended`
4. All existing tokens are immediately invalidated — users must re-authenticate

### Database Password Rotation

1. Update the password in the database
2. Update the Kubernetes Secret
3. Restart the affected services

---

## Rules

- ❌ Never hardcode secrets in source code
- ❌ Never commit `.env` files
- ❌ Never put secrets in Helm `values.yaml` — use `--set-string` or sealed secrets
- ✅ Use `openssl rand -hex 32` for all new secrets
- ✅ Rotate secrets on any suspected breach immediately
- ✅ Use RBAC to limit which pods can access which Secrets
