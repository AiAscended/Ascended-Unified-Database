# Developer Guide

---

## Local Development Setup

### 1. Clone and Configure

```bash
git clone https://github.com/AiAscended/Ascended-Unified-Database.git
cd Ascended-Unified-Database
cp .env.example .env
# Edit .env — at minimum set JWT_SECRET_KEY and POSTGRES_PASSWORD
```

### 2. Start the Dev Stack

```bash
docker compose -f docker/docker-compose.dev.yml up -d
```

### 3. Install Gateway Dependencies (for local development)

```bash
cd gateway
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the Gateway Locally

```bash
cd gateway
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Run the Admin Backend Locally

```bash
cd admin/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 6. Run the Admin Frontend Locally

```bash
cd admin/frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## Adding a New Database Provider

### Step 1 — Create the provider module

```python
# gateway/app/providers/mydb_provider.py

from __future__ import annotations
from typing import Any
from app.models.requests import GatewayRequest


class MyDBProvider:
    """Provider for MyDB — implements relevant capabilities."""

    def __init__(self, host: str, port: int, **kwargs: Any) -> None:
        self._host = host
        self._port = port
        self._client: Any = None

    async def connect(self) -> None:
        """Initialize the connection. Called at gateway startup."""
        import mydb_client
        self._client = await mydb_client.connect(host=self._host, port=self._port)

    async def disconnect(self) -> None:
        """Close the connection. Called at gateway shutdown."""
        if self._client:
            await self._client.close()

    async def query(self, request: GatewayRequest) -> Any:
        """Execute a query against MyDB."""
        return await self._client.execute(request.data.get("query", ""))
```

### Step 2 — Register in the router

```python
# gateway/app/services/router.py — add to route_request()

elif operation == "mydb_query":
    return await mydb_provider.query(request)
```

### Step 3 — Add to environment configs

```yaml
# configs/enterprise.yaml
databases:
  mydb:
    enabled: true
    host: mydb
    port: 12345
```

### Step 4 — Add to Docker Compose

```yaml
# docker/docker-compose.enterprise.yml
services:
  mydb:
    image: mydb:latest
    ports:
      - "12345:12345"
```

### Step 5 — Add to K8s manifests

```yaml
# k8s/databases/mydb-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mydb
  namespace: ascended
# ... standard deployment spec
```

---

## Validation Toolchain

Run the full validation suite before committing:

```bash
bash tools/run_validation.sh
```

Or run individually:
```bash
cd tools
python validator/validator.py
```

Install pre-commit hooks:
```bash
pip install pre-commit
cp tools/pre-commit-config.yaml .pre-commit-config.yaml
pre-commit install
```

---

## Testing

```bash
# Gateway unit tests
cd gateway
pytest tests/ -v --cov=app

# Admin backend tests
cd admin/backend
pytest tests/ -v --cov=app

# Frontend lint
cd admin/frontend
npm run lint
```

---

## Code Style

- Python: `flake8` with max line length 120
- Python: `black` formatting (where configured)
- TypeScript: ESLint with `eslint-config-next`
- No TODOs, FIXMEs, or placeholder code in committed code
