# CI/CD Overview

Five GitHub Actions workflows automate the full software delivery pipeline.

---

## Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| `ci.yml` | Every push + PR | Lint, security scan, Docker build, unit tests |
| `validation.yml` | Every push + PR | Ascended Validator (config + placeholder checks) |
| `cd-dev.yml` | Push to `dev` branch | Deploy to dev K8s namespace |
| `cd-prod.yml` | Merge to `main` | Blue/green deploy to production (manual approval) |
| `cd-enterprise.yml` | Release tag `v*` | Canary rollout to enterprise environment |

---

## CI Pipeline (`ci.yml`)

Steps:
1. **Checkout** code
2. **Python lint** — `flake8` on `gateway/` and `admin/backend/`
3. **Security scan** — `bandit` for hardcoded secrets and unsafe patterns
4. **Dependency audit** — `pip-audit` for known CVEs
5. **Docker build** — builds gateway and admin backend images
6. **Unit tests** — `pytest` with coverage report

Required secrets in GitHub:
```
DOCKER_REGISTRY
DOCKER_USERNAME
DOCKER_PASSWORD
```

---

## CD Dev (`cd-dev.yml`)

- Triggered by push to the `dev` branch
- Builds and pushes Docker images tagged `:dev`
- Applies `k8s/overlays/dev` to the dev cluster
- No manual approval required

---

## CD Production (`cd-prod.yml`)

- Triggered by merge to `main`
- **Requires manual approval** in GitHub Environments (`production`)
- Uses **blue/green deployment** strategy
- Applies `k8s/overlays/prod`
- On failure: automatic rollback via `kubectl rollout undo`

---

## CD Enterprise (`cd-enterprise.yml`)

- Triggered by release tag matching `v*.*.*`
- Uses **canary rollout** (10% → 50% → 100% traffic)
- Applies `k8s/overlays/enterprise`
- Full observability enabled during rollout
- Rollback strategy: tag a new release with the previous version

---

## Required GitHub Secrets

| Secret | Used By | Description |
|--------|---------|-------------|
| `KUBECONFIG_DEV` | cd-dev | Kubeconfig for dev cluster |
| `KUBECONFIG_PROD` | cd-prod | Kubeconfig for prod cluster |
| `KUBECONFIG_ENTERPRISE` | cd-enterprise | Kubeconfig for enterprise cluster |
| `DOCKER_REGISTRY` | All | Container registry host |
| `DOCKER_USERNAME` | All | Registry username |
| `DOCKER_PASSWORD` | All | Registry password |

---

## Rollback

Production rollback:
```bash
kubectl rollout undo deployment/gateway -n ascended
kubectl rollout status deployment/gateway -n ascended
```

Or via GitHub Actions: re-run the `cd-prod.yml` workflow with the previous commit SHA.
