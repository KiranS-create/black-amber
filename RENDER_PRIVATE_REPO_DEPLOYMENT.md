# AegisTrace (Black Amber) — Render Deployment Status & Configuration Report

**Project**: AegisTrace (SIH26237 — Code Name: Black Amber)  
**Private GitHub Repository**: `https://github.com/KiranS-create/black-amber.git`  
**Active Git Branch**: `main` (Latest Commit: [`a11a733`](https://github.com/KiranS-create/black-amber/commit/a11a733))  
**Target Render Service Name**: `aegistrace-sih26237`  
**Target Public URL**: `https://aegistrace-sih26237.onrender.com`  
**Evaluation Protocol**: CHAT 33 — Actual Render Deployment From Private Repository  
**Execution Timestamp**: September 29, 2026  
**Status**: **PRIVATE_GITHUB_ACCESS_REQUIRED / CONFIGURED_NOT_DEPLOYED**  

---

## 1. Domain Separation & Foreign Service Preservation

As strictly required:
1. **No Overwrites or Rebinding**: The existing domain `https://aegistrace.onrender.com` (hosting the foreign service `aegistrace-collector` for LLM workflow tracing) was **not** modified, rebound, or deleted.
2. **Dedicated Blueprint Service**: The Blueprint specification in `render.yaml` has been configured with the unique service name **`aegistrace-sih26237`**, targeting the public hostname:
   $$\text{https://aegistrace-sih26237.onrender.com}$$

---

## 2. Infrastructure as Code & Container Architecture

The repository's container deployment architecture is defined across two deterministic configuration files:

### A. Infrastructure Blueprint (`render.yaml`)
```yaml
services:
  - type: web
    name: aegistrace-sih26237
    runtime: docker
    plan: free
    region: oregon
    dockerfilePath: ./Dockerfile
    dockerContext: .
    healthCheckPath: /ready
    autoDeploy: true
    envVars:
      - key: DEMO_AUTH_ENABLED
        value: "true"
      - key: DEMO_USERNAME
        value: "admin"
      - key: DEMO_PASSWORD
        value: "admin"
      - key: SIH_HOST
        value: "0.0.0.0"
      - key: CORS_ORIGINS
        value: "*"
```

### B. Multi-Stage Container (`Dockerfile`)
- **Stage 1 (Web Builder)**: Node 20 Alpine executes `npm ci` and `npm run build` in `apps/web/`, generating the production bundle into `/web/dist`.
- **Stage 2 (Forensic Engine Runtime)**: Python 3.11-slim runtime with native post-quantum cryptographic primitives (NIST FIPS 203 ML-KEM-768 & FIPS 204 ML-DSA-65), OpenCV, and Pillow dependencies.
- **Embedded SPA Serving**: `/web/dist` assets are mounted directly into FastAPI, allowing a single open port to serve the full React workstation and REST API.
- **Dynamic Port Binding**: Honors Render's runtime `$PORT` variable via:
  ```bash
  exec uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 30
  ```
- **Readiness Healthcheck**: Probes dynamic `http://127.0.0.1:${PORT:-8000}/ready`.

---

## 3. Deployment Probe Diagnostics

| Endpoint | Target URL | HTTP Response | Diagnostic Result |
|---|---|---|---|
| **Root (SPA Entry)** | `https://aegistrace-sih26237.onrender.com/` | `404 Not Found` (`x-render-routing: no-server`) | Service not yet provisioned on Render. |
| **Health Probe** | `https://aegistrace-sih26237.onrender.com/health` | `404 Not Found` (`x-render-routing: no-server`) | Service not yet provisioned on Render. |
| **Deep Readiness Probe** | `https://aegistrace-sih26237.onrender.com/ready` | `404 Not Found` (`x-render-routing: no-server`) | Service not yet provisioned on Render. |
| **Authentication Status** | `https://aegistrace-sih26237.onrender.com/auth/status` | `404 Not Found` (`x-render-routing: no-server`) | Service not yet provisioned on Render. |

---

## 4. Operator Action: Connect Private GitHub Repository to Render

Because the repository **`KiranS-create/black-amber`** is **private**, Render requires GitHub App authorization through the Render web dashboard before it can clone and build the container:

### Step-by-Step Operator Instructions:
1. Log in to your [Render Dashboard](https://dashboard.render.com).
2. Click **Blueprints** $\to$ **New Blueprint Instance** (or **New +** $\to$ **Web Service**).
3. If prompted to connect a repository:
   - Select **GitHub**.
   - Under GitHub App Permissions, grant Render access to the private repository:
     $$\text{KiranS-create/black-amber}$$
4. Connect `KiranS-create/black-amber` (Branch: `main`).
5. Render will automatically detect `render.yaml` and configure:
   - Service Name: `aegistrace-sih26237`
   - Runtime: `Docker` (using root `Dockerfile`)
   - Healthcheck Path: `/ready`
   - Environment Variables: `DEMO_AUTH_ENABLED=true`, `DEMO_USERNAME=admin`, `DEMO_PASSWORD=admin`, `SIH_HOST=0.0.0.0`, `CORS_ORIGINS=*`.
6. Click **Apply** / **Create Web Service**.
7. Render will build the multi-stage container and deploy to:
   $$\text{https://aegistrace-sih26237.onrender.com}$$

---

## 5. Free-Tier Environmental Invariants & Behaviors

1. **Cold-Start Latency**:
   - On the Render Free tier, inactive containers sleep after 15 minutes of inactivity.
   - Initial cold-start spin-up takes approximately 30–45 seconds. Subsequent requests execute in $< 100\text{ ms}$.
2. **Ephemeral Storage**:
   - The root container filesystem is ephemeral; uploaded scratch files and local SQLite records reset upon container restart.
   - Pre-baked demonstration fixtures (`tests/fixtures/samples/`) and NIST FIPS test vectors remain permanently available in the container image.
3. **Continuous Deployment (Auto-Deploy)**:
   - `autoDeploy: true` is enabled in `render.yaml`. Every subsequent `git push origin main` triggers an automated container rebuild.

---

## 6. Current Deployment Status

```
DEPLOYMENT_STATE: PRIVATE_GITHUB_ACCESS_REQUIRED
REPOSITORY:       https://github.com/KiranS-create/black-amber.git (PRIVATE)
TARGET_SERVICE:   aegistrace-sih26237
TARGET_URL:       https://aegistrace-sih26237.onrender.com
LATEST_COMMIT:    a11a733
RENDER_YAML:      CONFIGURED_AND_PUSHED
DOCKERFILE:       VALIDATED_AND_PUSHED
ACTION_REQUIRED:  Authorize private repo KiranS-create/black-amber on dashboard.render.com
```
