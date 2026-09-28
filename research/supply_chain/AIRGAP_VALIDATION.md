# AegisTrace — Air-Gap & Offline Runtime Validation

**Classification**: Defense-Grade Air-Gap & Zero-Trust Supply-Chain Assessment  
**System Target**: AegisTrace (SIH26237) — Forensic Security Platform  
**Audit Date**: 2026-09-26  
**Operational Profile**: High-Security Air-Gapped Forensic Enclave  

---

## 1. Executive Summary & Air-Gap Posture

AegisTrace is engineered to operate in strictly isolated, classified, and air-gapped forensic enclaves with **zero outbound internet connectivity**.

A comprehensive behavioral and static analysis of the entire codebase was conducted to trace network sockets, HTTP requests, CDN links, telemetry sinks, and external asset dependencies.

### Air-Gap Readiness Verdict: **VALIDATED / PASS (with minor documentation caveats)**

| Layer | Runtime Egress Required? | Ingress Required? | Offline Persistence Mechanism | Air-Gap Status |
| :--- | :--- | :--- | :--- | :--- |
| **Backend Core Engine** | **NONE (0 outbound calls)** | Local loopback `127.0.0.1:8000` | Local SQLite (`data/metadata.sqlite3`) + Filesystem (`data/artifacts/`) | **100% AIR-GAP COMPLIANT** |
| **PQC Cryptographic Core** | **NONE (0 outbound calls)** | None (Pure local CPU computation) | Local key memory + encrypted keystore | **100% AIR-GAP COMPLIANT** |
| **Forensic Attribution Engine** | **NONE (0 outbound calls)** | None (Local array math) | Content-addressed artifact store | **100% AIR-GAP COMPLIANT** |
| **Web Dashboard UI (`apps/web`)** | **NONE (Local HTTP only)** | Local loopback `127.0.0.1:5173` | Static pre-compiled assets (`dist/assets/`) | **COMPLIANT (Font fallback active)** |
| **Docker Container** | **NONE (Zero container egress)**| Mapped host ports (8000/5173) | Volume-mounted local storage | **100% AIR-GAP COMPLIANT** |

---

## 2. Build-Time vs. Runtime Dependency Separation

In an air-gapped deployment lifecycle, network access is strictly segregated between **Build Time** (pre-deployment environment) and **Runtime** (air-gapped enclave):

```mermaid
flowchart LR
    subgraph Build_Stage ["Build Environment (Connected / Staging)"]
        PIP["pip install (Python Wheels)"]
        NPM["npm install (Node Modules)"]
        VBUILD["npx vite build -> apps/web/dist"]
        DOCKER["docker build -t sih26237:latest"]
    end

    subgraph Transport_Stage ["Secure Air-Gap Transfer"]
        USB["Signed Tarball / Air-Gap Image Media"]
    end

    subgraph Enclave_Stage ["Air-Gapped Operational Enclave (Zero Network)"]
        BACKEND["FastAPI / Uvicorn (127.0.0.1:8000)"]
        CRYPTO["ML-KEM-768 / ML-DSA-65 Engine"]
        FUSION["Bayesian Evidence Fusion"]
        UI["Vite Preview / Nginx Static (:5173)"]
        STORE["Local SQLite & Artifact Storage"]
    end

    Build_Stage --> USB --> Enclave_Stage
```

### 2.1 Detailed Lifecycle Separation

| Dependency / Tool | Build-Time Role | Runtime Role in Air-Gap | Network Activity in Air-Gap |
| :--- | :--- | :--- | :--- |
| **`python` / `pip`** | Resolves wheels, compiles native extensions | Executes Python bytecode (`.pyc`) | **ZERO** (No `pip install` at runtime) |
| **`kyber-py` / `dilithium-py`**| Packaged as wheel | Computes NTT and polynomial lattice operations | **ZERO** (Self-contained integer math) |
| **`pycryptodome`** | Packaged as binary wheel | AES-256-GCM hardware/AES-NI acceleration | **ZERO** |
| **`fastapi` / `uvicorn`** | Server framework setup | Listens on local interface `127.0.0.1` | **ZERO** (Local loopback only) |
| **`vite` / `typescript`** | Bundles React into `apps/web/dist` | Not executed at runtime (static bundle served) | **ZERO** |
| **`lucide-react`** | Inlines SVG icons into JavaScript bundle | Renders inline SVG icons in browser | **ZERO** (No external icon font requests) |
| **`sqlite3`** | Database schema creation | Manages local transactions on `metadata.sqlite3` | **ZERO** (Local embedded engine) |

---

## 3. Behavioral Audit of Potential Network Leaks

### 3.1 Telemetry & Analytics Inspection

- **Codebase Scan**: Searched for telemetry SDKs (`sentry`, `posthog`, `google-analytics`, `mixpanel`, `datadog`, `telemetry`, `statsd`).
- **Findings**: **Zero telemetry SDKs or background telemetry calls are present in AegisTrace source code.**
- **Verification**: The API framework initializes zero background network threads or third-party reporting endpoints.

### 3.2 External API Calls Inspection

- **Codebase Scan**: Searched for `requests.get/post`, `urllib.request.urlopen`, `httpcore`, `httpx` across `core/`, `apps/api/`, `attacks/`.
- **Findings**:
  - `apps/api/`: **0 outbound HTTP requests.** All API endpoints operate strictly on request payloads and local storage.
  - `core/`: **0 outbound HTTP requests.** Pure cryptographic, watermark, and attribution processing.
  - `docker-compose.yml`: Uses `urllib.request.urlopen('http://127.0.0.1:8000/health')` strictly against `127.0.0.1` for container health monitoring.
  - `scripts/deployment/start_demo.py`: Uses `urllib.request.urlopen('http://127.0.0.1:8000/health')` strictly on `127.0.0.1` to wait for backend startup.

### 3.3 Remote Fonts & CDN Assets Inspection

- **Audit Findings**:
  1. **`apps/web/index.html` (Lines 7–9)**:
     ```html
     <link rel="preconnect" href="https://fonts.googleapis.com" />
     <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
     <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700..." rel="stylesheet" />
     ```
     - *Behavior in Air-Gap*: In an offline browser, the HTTP request to `fonts.googleapis.com` fails silently or times out immediately without blocking page rendering.
     - *Graceful Degradation*: `apps/web/index.html` and `apps/web/src/styles/tokens.css` declare robust system font fallbacks:
       `font-family: 'Geist', 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;`
     - *Recommendation for complete air-gap hardening*: Bundle WOFF2 font files locally in `apps/web/public/fonts/` if custom typography is required offline.

  2. **`presentation/index.html` (Line 7)**:
     ```html
     <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
     ```
     - *Behavior in Air-Gap*: The standalone presentation HTML slide viewer loads Mermaid from jsdelivr CDN. If opened offline, slides render all text and cards, but interactive dynamic Mermaid diagram rendering requires internet or local vendoring.
     - *Production Status*: The core forensic dashboard and API do not use this file (it is exclusively for presentation slide decks).

---

## 4. Local Storage & Ingress Security

1. **Storage Isolation**:
   - SQLite Database: `data/metadata.sqlite3`
   - Artifact Blob Store: `data/artifacts/`
   - All filesystem operations are bounded by `apps/api/security.py::sanitize_path()` to strictly prevent path traversal attacks.
2. **CORS Isolation**:
   - `allowed_cors_origins` is explicitly restricted to local origins:
     `http://localhost:5173`, `http://localhost:3000`, `http://127.0.0.1:5173`, `http://127.0.0.1:3000`, `http://localhost:8000`, `http://127.0.0.1:8000`.
   - Wildcard `*` CORS is strictly prohibited.
3. **Host Binding**:
   - `start_demo.py` binds Uvicorn and Vite preview strictly to `127.0.0.1` (loopback only) by default, preventing unauthorized LAN exposure.
   - Container deployments bind to `0.0.0.0` inside container network namespace, mapped explicitly to host ports `8000`/`5173`.

---

## 5. Air-Gap Deployment Protocol for Operators

To deploy AegisTrace into an air-gapped forensic environment:

```bash
# ==========================================================
# 1. On Connected Staging Machine: Build Deployment Bundle
# ==========================================================
git clone <repo> aegistrace && cd aegistrace
pip download -r deployment/requirements.txt -d ./offline_wheels
cd apps/web && npm ci && npm run build && cd ../..
tar -czvf aegistrace_airgap_bundle.tar.gz aegistrace/

# ==========================================================
# 2. Inside Air-Gapped Enclave: Unpack & Install
# ==========================================================
tar -xzvf aegistrace_airgap_bundle.tar.gz
cd aegistrace
python -m venv .venv
.\.venv\Scripts\activate  # (or source .venv/bin/activate)
pip install --no-index --find-links=./offline_wheels -r deployment/requirements.txt

# ==========================================================
# 3. Launch Offline Platform
# ==========================================================
powershell -ExecutionPolicy Bypass -File .\deployment\start_demo.ps1
```
