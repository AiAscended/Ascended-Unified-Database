# Security Architecture

## Threat Model

The system is designed to defend against:

1. **Unauthorized data access** — JWT + RBAC on every request
2. **Direct database access** — NetworkPolicy blocks all external database connections
3. **Secrets exposure** — No hardcoded credentials; Kubernetes Secrets in production
4. **Injection attacks** — Parameterized queries throughout; input validated by Pydantic
5. **DoS** — Rate limiting at the gateway; HPA for automatic scaling
6. **Token forgery** — HS256 JWT with a strong secret; short expiry (60 min default)

---

## Defense Layers

```
[Internet]
    ↓
[Ingress + TLS (Let's Encrypt)]
    ↓
[Gateway: JWT verification + RBAC + rate limiting]
    ↓
[Internal network — databases not externally accessible]
    ↓
[Kubernetes NetworkPolicy — databases accept only from gateway namespace]
```

---

## Kubernetes Security

### NetworkPolicy

```yaml
# k8s/security/network-policies.yaml
# Databases only accept traffic from the ascended namespace
ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: ascended
```

### PodSecurity

```yaml
# k8s/security/pod-security.yaml
# Non-root containers, read-only filesystem, no privilege escalation
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```

---

## Gateway Security Headers

The gateway adds security headers to all responses:

```python
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=63072000; includeSubDomains
```

---

## Rate Limiting

Default: 100 requests/minute per authenticated user.

Admin-role users: 500 requests/minute.

Exceeded: `429 Too Many Requests` with `Retry-After` header.

Configure via:
```yaml
# configs/prod.yaml
security:
  rate_limit_per_minute: 100
```

---

## Audit Log

Every administrative action is recorded in the `audit_log` table with:
- User ID
- Action performed
- Resource type and ID
- IP address
- Timestamp
- Success/failure status

The audit log is append-only and viewable via the Admin Panel at `/audit`.
