# AegisTrace Live Deployment Status

```
================================================================================
DEPLOYMENT STATUS: DEPLOYED_AND_VERIFIED
PROVIDER:          Cloudflare Edge Network (Quick Tunnel) + Single-Port FastAPI
MONTHLY COST:      $0.00 (Zero-Cost Free Tier)
PUBLIC URL:        https://joan-enforcement-whatever-looks.trycloudflare.com
LAST VERIFIED:     September 28, 2026
TEST PASS RATE:    27/27 API Tests (100%), Playwright E2E Browser Suite (100%)
================================================================================
```

---

## 1. Quick Access for Evaluators

| Parameter | Value |
|---|---|
| **Public Endpoint** | [`https://joan-enforcement-whatever-looks.trycloudflare.com`](https://joan-enforcement-whatever-looks.trycloudflare.com) |
| **Demo Username** | `admin` |
| **Demo Password** | `admin` |
| **Demo Tenant** | `demo_tenant` (Isolated evaluation sandbox) |
| **Autofill Support** | One-click **Autofill** button on login screen |
| **Offline Verifier** | Standalone zero-server verifier accessible via login footer |

---

## 2. Platform Architecture & Scope

AegisTrace operates as an all-in-one single-port web workstation:

- **Frontend**: Vite 5 + React 18 SPA embedded in FastAPI static files (`apps/web/dist`).
- **Backend**: FastAPI (Python 3.9+) with SQLite, PQC engines (ML-KEM-768 / ML-DSA-65), Tardos collusion-resistant tracing, and RFC-6962 Merkle tree ledger.
- **Reverse Proxy / Edge**: Cloudflare edge network via `cloudflared` tunnel with automatic SSL/TLS termination and DDoS mitigation.
- **Platform Scope Notice**: Web application and REST API are fully productized. Standalone desktop packaging (Windows `.exe`, macOS `.dmg`) and Android mobile packaging are explicitly **DEFERRED TO FUTURE WORKSTREAM**.

---

## 3. Verified Invariants

- [x] **HTTPS Everywhere**: TLS 1.3 enforced with `Strict-Transport-Security`.
- [x] **Zero Server Leaks in Production**: With `DEMO_AUTH_ENABLED=false`, `admin/admin` credentials fail with HTTP 401 Unauthorized; production database starts completely clean (0 documents, 0 releases, 0 ledger events).
- [x] **Pre-Loaded Scenarios**: 4 adversarial scenarios (clean digital leak, Gaussian blur, print-scan, 3-traitor Tardos collusion) execute in demo mode with real Bayesian attribution.
- [x] **Progressive Disclosure**: Technical evidence displays Dirichlet priors, LLR thresholds, and Merkle tree inclusion proofs upon expanding `[ Technical details ]`.
- [x] **Standalone Verifier**: Supports offline evidence verification of signed `.zip` archives directly against 12 cryptographic forensic pillars.
- [x] **Honest Registration**: Self-service registration returns HTTP 403 Forbidden alert explaining that public registration is closed in this deployment.
