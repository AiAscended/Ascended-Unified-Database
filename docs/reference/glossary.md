# Glossary

| Term | Definition |
|------|-----------|
| **Capability** | An abstract database operation (e.g. `vector_search`, `transactional_write`) that services request without knowing which database fulfils it |
| **Provider** | A Python module that wraps one database type (Postgres, Redis, Qdrant, etc.) and implements one or more capabilities |
| **Data Gateway** | The single API layer through which all services access databases. Runs on port 8000. |
| **Admin Panel** | The web-based administration interface for managing databases, users, metrics, and config. Runs on ports 8001 (API) and 3001 (UI). |
| **Environment** | A named tier (`dev`, `production`, `enterprise`) that defines which databases are available and how they are configured |
| **Capability-based routing** | The gateway pattern where services request a *capability* and the gateway selects the correct provider based on the active environment |
| **pgvector** | A Postgres extension that adds vector storage and similarity search. Used in dev as a lightweight alternative to Qdrant. |
| **JWT** | JSON Web Token — the auth mechanism used by both the gateway and admin API |
| **RBAC** | Role-Based Access Control — the permission model with four roles: viewer, developer, operator, admin |
| **HPA** | Horizontal Pod Autoscaler — Kubernetes resource that scales gateway pods based on CPU/memory |
| **KEDA** | Kubernetes Event-Driven Autoscaling — scales pods based on Kafka lag and other event sources |
| **Kustomize** | A Kubernetes-native configuration tool used to apply environment overlays to base manifests |
| **Overlay** | A Kustomize directory that patches the base K8s manifests for a specific environment |
| **Helm chart** | A package of Kubernetes manifests with a `values.yaml` for configuration |
| **StatefulSet** | A Kubernetes workload resource for stateful applications like Postgres and Kafka that need stable network identities and persistent storage |
| **AscendedStack** | The full ecosystem of AI-OS, Agents, Models, Orchestration, Search, Content, SDK, Deployment, and Control Plane repositories |
| **pgpool** | The admin-maintained table of database connection registrations stored in Postgres |
| **Audit log** | A tamper-evident record of all administrative actions performed on the platform |
| **WebSocket stream** | Real-time data push from the admin backend to the frontend dashboard |
| **Loki** | Grafana's log aggregation system used to collect and query container logs |
| **Jaeger** | A distributed tracing system used to track requests through the gateway and database calls |
