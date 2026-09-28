# Self-Hosted Container Deployment (Docker & Compose)

> **Platform Scope**: Production Web Architecture with Multi-Stage Container.  
> **Desktop Status**: Standalone desktop installers (.exe/.dmg) are **DEFERRED TO FUTURE WORKSTREAM**. Containerized self-hosting provides an identical isolated operating environment accessible via modern web browsers.

---

## 1. Architecture Overview

AegisTrace employs a multi-stage Docker build:
- **Stage 1 (`web-builder`)**: Node 20 Alpine environment compiling the TypeScript/Vite frontend into `/web/dist`.
- **Stage 2 (`runtime`)**: Minimal Python 3.11 Slim environment with post-quantum cryptographic libraries (libgl, libglib, kyber-py, dilithium-py).
- FastAPI serves both the static web assets (`/`, `/assets/*`) and the REST API (`/auth/*`, `/system/*`, `/evidence/*`, `/ready`).

```mermaid
flowchart LR
    A[git clone / source] --> B[Stage 1: node:20-alpine]
    B -->|npm run build| C[/web/dist]
    A --> D[Stage 2: python:3.11-slim]
    C -->|COPY --from=web-builder| D
    D --> E[Single Container Image :8000]
    E --> F[Client Browser]
```

---

## 2. Quickstart: One-Command Deployment

From the repository root:

```bash
docker compose up -d --build
```

Verify that the container is healthy:
```bash
docker compose ps
```
Output:
```
NAME                    IMAGE                  COMMAND                  SERVICE      CREATED         STATUS                   PORTS
aegistrace-workstation  sih26237-aegistrace    "uvicorn apps.api.ma…"   aegistrace   5 seconds ago   Up 5 seconds (healthy)   0.0.0.0:8000->8000/tcp
```

Access the application in your browser:
```
http://localhost:8000
```

---

## 3. Configuration via Environment Variables

All configuration can be customized via `.env` or in `docker-compose.yml`:

| Variable | Default | Purpose |
|---|---|---|
| `DEMO_AUTH_ENABLED` | `false` | Enable `admin/admin` judge login |
| `DEMO_USERNAME` | `admin` | Demo username |
| `DEMO_PASSWORD` | `admin` | Demo password |
| `DEMO_TENANT_ID` | `demo_tenant` | Storage namespace for synthetic records |
| `SIH_PORT` | `8000` | Port bound inside container |
| `CORS_ORIGINS` | `*` | Allowed CORS origins for external API access |

### Enabling SIH Judge Demo Access
To enable demonstration access for hackathon judges:
```bash
# In .env
DEMO_AUTH_ENABLED=true
```
Then restart the container:
```bash
docker compose up -d
```

---

## 4. Volume Persistence

The `docker-compose.yml` mounts two named persistent volumes:
1. `aegistrace-data`: Stores SQLite ledger databases, event logs, and recipient registries.
2. `aegistrace-artifacts`: Stores encrypted payloads and forensic evidence packages.

To back up data from the volumes:
```bash
docker run --rm -v sih26237_aegistrace-data:/data -v $(pwd):/backup alpine tar czf /backup/aegistrace-data-backup.tar.gz -C /data .
```

---

## 5. Healthcheck & Diagnostics

The container exposes two health probes:
- `GET /health`: Shallow liveness probe (returns `{ "status": "healthy" }`).
- `GET /ready`: Deep readiness probe verifying database writability, artifact directory access, PQC engine initialization, and ledger state.

Test probe manually:
```bash
curl -i http://localhost:8000/ready
```
Expected response (`HTTP 200 OK`):
```json
{
  "status": "ready",
  "timestamp": "2026-09-28T09:30:00Z",
  "components": {
    "database": { "status": "healthy", "writable": true },
    "artifacts_storage": { "status": "healthy", "writable": true },
    "crypto_provider": { "status": "healthy", "pqc_enabled": true },
    "orchestrator": { "status": "healthy", "initialized": true }
  }
}
```
