# AegisTrace Deployment Architecture & Operations Guide

> **Target Platform**: Production Web Application & Independent Offline Verifier  
> **Platform Status**: Web Workstation is the primary production target. Desktop (Windows `.exe`, macOS `.dmg`) and Mobile (Android `.apk`) distributions are **DEFERRED TO FUTURE WORKSTREAM**.

---

## 1. Overview of Deployment Topologies

AegisTrace supports four primary deployment operational models, ranging from local evaluation to zero-cost cloud hosting and air-gapped forensic environments:

| Deployment Model | Primary Use Case | Hosting Cost | Complexity | Security Posture |
|---|---|---|---|---|
| **Local Evaluation** | Developer testing, SIH judge evaluation | $0 | Low | Single workstation |
| **Self-Hosted Docker** | Enterprise intranet, forensic labs | Server cost | Low | Isolated containers with volumes |
| **Free Cloud Hosting** | Public demonstrations, remote judging | $0 / mo | Moderate | Managed multi-tenant or container |
| **Air-Gapped Sovereign** | Classified intelligence operations | $0 (Hardware) | Moderate | 100% offline, zero internet |

---

## 2. Guide Directory

1. [**LOCAL.md**](./LOCAL.md) — Local development, test execution, and fast evaluation.
2. [**DOCKER.md**](./DOCKER.md) — Docker and Docker Compose containerized deployment.
3. [**FREE_HOSTING.md**](./FREE_HOSTING.md) — Step-by-step $0/mo deployment on Render, Fly.io, Hugging Face Spaces, and Vercel/Cloudflare Pages.
4. [**HTTPS.md**](./HTTPS.md) — TLS/SSL termination with reverse proxies (Caddy, Nginx, Cloudflare).
5. [**BACKUP_RESTORE.md**](./BACKUP_RESTORE.md) — Cryptographic backup and restoration of immutable ledger events and evidence records.
6. [**OFFLINE.md**](./OFFLINE.md) — Deployment in strict air-gapped environments with pre-bundled dependencies and offline verification.

---

## 3. Core Operational Invariants

Regardless of deployment topology, AegisTrace enforces the following invariants:

1. **Zero Fake Data in Production**: Workspaces initialize completely clean. Demo records are strictly isolated in `demo_tenant` and accessible only when `DEMO_AUTH_ENABLED=true`.
2. **Post-Quantum Security**: Key encapsulation utilizes NIST FIPS 203 ML-KEM-768; signatures utilize NIST FIPS 204 ML-DSA-65.
3. **Fail-Closed Attribution**: If forensic signal margin $\Delta < 2.50$ LLR, the system explicitly abstains rather than falsely accusing a candidate.
4. **Independent Offline Verification**: Evidence packages (`.zip` archives with canonical `manifest.json`) can be verified by judicial auditors using `AegisTrace Verify` without network connectivity.
