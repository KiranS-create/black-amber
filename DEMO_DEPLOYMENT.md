# Demonstration Deployment Guide (SIH Judge Evaluation)

> **Primary Live Demonstration**: [Render Web Service (https://aegistrace.onrender.com)](https://aegistrace.onrender.com)  
> **Active Edge Mirror**: [`https://joan-enforcement-whatever-looks.trycloudflare.com`](https://joan-enforcement-whatever-looks.trycloudflare.com)  
> **Deployment Status**: `DEPLOYED_AND_BROWSER_VERIFIED`  
> **Demo Credentials**: `admin` / `admin` (Autofill enabled)  
> **Platform Status**: Production Web Workstation. Standalone desktop applications (Windows `.exe`, macOS `.dmg`) and Android mobile packaging are **DEFERRED TO FUTURE WORKSTREAM**.

---

## 0. Instant Online Evaluation (Zero Local Setup)

Jury members and evaluators can immediately access the live AegisTrace demo workstation without installing Docker or running local processes:

- **Primary Cloud URL (Render)**: [`https://aegistrace.onrender.com`](https://aegistrace.onrender.com)
- **Active Edge Mirror**: [`https://joan-enforcement-whatever-looks.trycloudflare.com`](https://joan-enforcement-whatever-looks.trycloudflare.com)
- **Login Credentials**: Username: `admin` | Password: `admin` (or click **Autofill** on the login screen).
- **Environment**: Isolated `demo_tenant` pre-loaded with the 4 benchmark adversarial evaluation scenarios.
- **Evaluator Guide**: Step-by-step instructions available in [HOSTED_DEMO_RUNBOOK.md](HOSTED_DEMO_RUNBOOK.md).

---

## 1. Quick Local Docker Launch for Evaluators

Deploy an isolated demonstration instance with one command:

```bash
docker run -d \
  --name aegistrace-demo \
  -p 8000:8000 \
  -e DEMO_AUTH_ENABLED=true \
  -e DEMO_USERNAME=admin \
  -e DEMO_PASSWORD=admin \
  -e DEMO_TENANT_ID=demo_tenant \
  sih26237-aegistrace:latest
```

Then navigate to:
```
http://localhost:8000
```

---

## 2. Demonstration Authentication Workflow

1. On the login screen, notice the **DEMO ACCESS** helper card:
   - Username: `admin`
   - Password: `admin`
2. Click **Autofill** to instantly populate credentials, then click **Sign in**.
3. Upon entering the workstation, an unambiguous yellow **DEMO DATA** badge indicates that you are operating inside the synthetic evaluation tenant (`demo_tenant`).
4. At any time during the evaluation, click **[ Clear demo data ]** to reset the tenant to a clean state.

---

## 3. Pre-Loaded Evaluation Scenarios

The demonstration tenant includes 4 pre-configured adversarial benchmarks ready for single-click investigation:

| Scenario ID | Name | Adversarial Transformation | Expected Forensic Outcome |
|---|---|---|---|
| `clean_bob` | Clean Digital Leak | Unaltered decrypted PDF | **Attributed to Bob** (LLR +36.20, Separation $\Delta = 18.40$) |
| `gaussian_blur` | Blurred Camera Photo | 5x5 Gaussian blur, contrast degradation | **Attributed to Bob** (LLR +24.80, DSSS spatial carrier demodulated) |
| `print_scan` | Physical Print-Scan | Rotation, halftoning, scanner sensor noise | **Attributed to Bob** (LLR +18.60, Robust physical watermark extracted) |
| `tardos_collusion`| 3-Traitor Collusion | Bob + Charlie + Dave interleaved synthesis | **Collusion Detected** (Tardos score identifies all 3 traitors; abstain guard fires if ambiguous) |

---

## 4. Demonstrating the 6 Core Actions

Judges can execute the full end-to-end lifecycle in under 2 minutes:

1. **Import artifact**: Navigate to **Documents** -> Click `[ Import artifact ]` -> Upload sample contract.
2. **Protect artifact**: Click `Authorize encrypted release` -> Select Alice, Bob, Charlie -> Sealed under ML-KEM-768.
3. **Decapsulate**: Simulate Bob decrypting his assigned package -> ML-DSA-65 signed provenance event created on ledger.
4. **Investigate leak**: Navigate to **Investigations** -> Select `Evaluate benchmark: Clean digital leak` -> Bayesian engine computes log-likelihood ratio scores across spatial, Tardos, signature, and ledger channels.
5. **Verify package**: Navigate to **AegisTrace Verify** -> Drag & drop `evidence_package.zip` -> Verifies post-quantum signatures and Merkle root.
6. **Export dossier**: Click `[ Export evidence dossier ]` in the top right -> Generates audit report.
