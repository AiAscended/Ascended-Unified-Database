# Security — Authentication

## JWT Token Flow

All gateway and admin API requests require a valid JWT Bearer token.

### 1. Obtain a Token

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password&grant_type=password"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Use the Token

```bash
curl http://localhost:8000/gateway/query \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{ "operation": "transactional_read", "data": { "query": "SELECT 1" } }'
```

### 3. Token Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | — (required) | HMAC secret. Must be ≥ 32 bytes |
| `JWT_ALGORITHM` | `HS256` | Signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |

Generate a secure key:
```bash
openssl rand -hex 32
```

---

## API Keys (Alternative to JWT)

API keys are stored in the `api_keys` table with a hashed secret. They are scoped to a workspace and carry rate limits.

```bash
# Create via admin API
curl -X POST http://localhost:8001/admin/api/keys \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "name": "CI/CD Key", "scopes": ["gateway:read", "gateway:write"] }'
```

Use the returned `key` value as a Bearer token.

---

## Token Rotation

Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`. The client must request a new token before expiry. There is no refresh token mechanism — request a new token from `/auth/token`.

For automated systems, use API keys with long-lived rotation schedules instead.
