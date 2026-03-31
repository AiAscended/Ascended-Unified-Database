# Security — Authorization (RBAC)

## Role Model

| Role | Description | Gateway | Admin API | User Mgmt | Config |
|------|-------------|---------|-----------|-----------|--------|
| `admin` | Full platform access | ✅ All ops | ✅ Full | ✅ | ✅ |
| `operator` | Operational access | ✅ All ops | ✅ Read + deploy | ❌ | ✅ Read |
| `developer` | Development access | ✅ All ops | ✅ Read | ❌ | ❌ |
| `viewer` | Read-only | ✅ Read ops only | ✅ Read | ❌ | ❌ |

## Role Assignment

Assign roles via the Admin Panel UI (`/users`) or the API:

```bash
curl -X POST http://localhost:8001/admin/api/users/{id}/role \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "role": "developer" }'
```

## Gateway Operation Permissions

| Operation | viewer | developer | operator | admin |
|-----------|--------|-----------|----------|-------|
| `transactional_read` | ✅ | ✅ | ✅ | ✅ |
| `vector_search` | ✅ | ✅ | ✅ | ✅ |
| `cache_get` | ✅ | ✅ | ✅ | ✅ |
| `transactional_write` | ❌ | ✅ | ✅ | ✅ |
| `cache_set` | ❌ | ✅ | ✅ | ✅ |
| `file_retrieve` | ✅ | ✅ | ✅ | ✅ |
| `file_store` | ❌ | ✅ | ✅ | ✅ |
| `graph_query` | ✅ | ✅ | ✅ | ✅ |
| `analytics_query` | ✅ | ✅ | ✅ | ✅ |
| `stream_publish` | ❌ | ✅ | ✅ | ✅ |
