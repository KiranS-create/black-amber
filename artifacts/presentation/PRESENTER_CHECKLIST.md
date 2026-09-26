# SIH26237 — Presenter Pre-Flight Checklist & Demo Failsafe Guide

**Author:** Systems Integration & Presentation Lead  
**Classification:** Operational Runbook  

---

## 1. Pre-Flight Setup Checklist (T-Minus 15 Minutes)

Complete every item before stepping in front of judges:

- [ ] **1. Clean Machine Validation**
  - Verify Python version is $\ge 3.9$: `python --version`
  - Verify Node.js is $\ge 18$: `node -v`

- [ ] **2. Dependency & Environment Health Check**
  - Run the automated health check:
    ```powershell
    python scripts/deployment/health_check.py
    ```
  - Verify output shows: `DEPLOYMENT HEALTH VERDICT: PASS`.

- [ ] **3. Port Availability**
  - Verify Port `8000` (FastAPI) and Port `5173` (Vite UI) are not in use by other processes.

- [ ] **4. Demo Environment Reset & Fixtures Generation**
  - Execute a clean environment reset:
    ```powershell
    .\deployment\reset_demo.ps1
    ```
    *Or via Python:* `python scripts/deployment/reset_demo.py`
  - Verify that `data/demo_fixtures/` contains:
    - `source_document.pdf`
    - `bob_leak.pdf`
    - `tampered_leak.pdf`
    - `clean_document.pdf`
    - `manifest.json`

- [ ] **5. Start Interactive Stack**
  - Execute:
    ```powershell
    .\deployment\start_demo.ps1
    ```
  - Confirm browser opens to `http://127.0.0.1:5173`.
  - Confirm API Swagger docs are reachable at `http://127.0.0.1:8000/docs`.

---

## 2. Demo Modes & Switch Rules

The presenter has three built-in execution tiers:

```
  +--------------------+        If Web UI / Port Issue        +--------------------+
  |  MODE 1: LIVE UI   |  ─────────────────────────────────►  | MODE 2: SCRIPT RUN |
  | (Vite + FastAPI)   |                                      | (run_live_demo.py) |
  +--------------------+                                      +--------------------+
                                                                        │
                                                                        │ If Terminal GUI / Rich Fails
                                                                        ▼
                                                              +--------------------+
                                                              | MODE 3: CLI BACKUP |
                                                              | (run_demo_cli.py)  |
                                                              +--------------------+
```

### **CRITICAL RULE ON MODE SWITCHING**
> [!CAUTION]
> **NEVER SILENTLY SWITCH MODES.**
> If switching from Mode 1 (Live UI) to Mode 2 (Script) or Mode 3 (CLI Fallback), **explicitly announce the change to judges**:
> *"Judges, to show the underlying cryptographic execution directly in the terminal, we will execute our live command-line forensic harness."*

---

## 3. Demo Failsafe & Recovery Playbook

### **Scenario A: Port 8000 or 5173 is Busy**
- **Symptom:** `Address already in use` error.
- **Fix:**
  ```powershell
  # Kill lingering uvicorn/node processes
  Get-Process -Name python, node -ErrorAction SilentlyContinue | Stop-Process -Force
  .\deployment\start_demo.ps1
  ```

### **Scenario B: Web Browser Hangs or Displays White Screen**
- **Symptom:** Frontend UI fails to render.
- **Fix:**
  1. Refresh with `Ctrl + F5` (hard reload).
  2. If problem persists, switch to **Mode 2 (Deterministic Python Runner)**:
     ```powershell
     python scripts/demo/run_live_demo.py
     ```

### **Scenario C: Database Lock / SQLite Error**
- **Symptom:** `sqlite3.OperationalError: database is locked`.
- **Fix:**
  ```powershell
  python scripts/deployment/reset_demo.py
  ```

---

## 4. Presenter Screen Setup

- **Left Half of Screen (50%):** Web Browser at `http://127.0.0.1:5173`.
- **Right Half of Screen (50%):** PowerShell Terminal showing real-time FastAPI Uvicorn logs (`[INFO] POST /analyze/leak 200 OK`).
- **Secondary Display / Notes:** `presentation/index.html` with Speaker Notes toggled (`N`).
