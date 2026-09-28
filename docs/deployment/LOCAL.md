# Local Deployment & Development Guide

> **Scope**: Local evaluation and rapid verification on developer workstations.  
> **Desktop Status**: Native Windows `.exe` / macOS `.dmg` installers are **DEFERRED TO FUTURE WORKSTREAM**. All workstation capabilities run locally via your browser connecting to the local backend.

---

## 1. Prerequisites

- **Python**: Version 3.9, 3.10, or 3.11
- **Node.js**: Version 18+ or 20+ (with `npm`)
- **Git**

---

## 2. Environment Setup

### 2.1 Backend Environment Setup

1. Open a terminal in the repository root (`C:\Projects\SIH26237` or repo path):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r deployment/requirements-lock.txt
   ```

3. Configure environment variables:
   ```bash
   # Copy sample configuration
   cp .env.example .env
   ```
   For local demonstration evaluation by SIH judges, ensure:
   ```env
   DEMO_AUTH_ENABLED=true
   DEMO_USERNAME=admin
   DEMO_PASSWORD=admin
   DEMO_TENANT_ID=demo_tenant
   SIH_PORT=8000
   ```

4. Start the backend server:
   ```bash
   python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend will start and log:
   ```
   INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   ```

### 2.2 Frontend Environment Setup

1. Open a second terminal window:
   ```bash
   cd apps/web
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The development server will provide access at `http://localhost:5173`.

---

## 3. Production Single-Port Serving

You can compile the frontend bundle once and have FastAPI serve both the REST API and the single page application from port `8000`:

```bash
# 1. Build frontend bundle
cd apps/web
npm run build

# 2. Return to root and launch backend
cd ../..
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000` in any modern web browser (Chrome, Firefox, Safari, Edge).

---

## 4. Verification & Testing

Execute the API test suite to verify cryptographic primitives and authentication behavior:

```bash
pytest tests/api/test_api_auth_and_product.py -v
```

All 8 tests must pass:
- `test_demo_login_success_when_enabled`
- `test_demo_login_rejected_when_disabled`
- `test_demo_login_bad_password`
- `test_standard_token_login`
- `test_auth_status_endpoint`
- `test_registration_disabled_returns_403`
- `test_system_ready_endpoint`
- `test_verify_corrupted_package`
