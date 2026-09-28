# Air-Gapped & Sovereign Offline Deployment

> **Platform Scope**: Air-Gapped Sovereign Forensic Installations.  
> **Desktop Status**: Standalone native desktop distributions are **DEFERRED TO FUTURE WORKSTREAM**. The web application and independent offline verifier operate 100% offline within a local air-gapped browser.

---

## 1. Zero External Connectivity Principle

AegisTrace is engineered from the ground up to operate in **pure air-gapped security enclaves**:
- **Zero Cloud API Dependencies**: Does not rely on OpenAI, Anthropic, AWS KMS, Google Cloud, or external services.
- **Self-Contained Post-Quantum Crypto**: NIST FIPS 203 (ML-KEM-768) and FIPS 204 (ML-DSA-65) execute locally in native C/Python.
- **Embedded Browser Runtime**: The Web Workstation is delivered directly as static HTML/JS/CSS from the local container or local Python process to `http://localhost:8000`.

---

## 2. Air-Gapped Package Preparation (Connected Machine)

On an internet-connected workstation, bundle the complete offline container or wheels:

### 2.1 Option A: Docker Image Export (Recommended)
```bash
# 1. Build the production multi-stage container
docker build -t aegistrace:airgap-release .

# 2. Export to a tarball archive
docker save aegistrace:airgap-release -o aegistrace_airgap_image.tar

# 3. Compute cryptographic verification hash
sha256sum aegistrace_airgap_image.tar > aegistrace_airgap_image.tar.sha256
```

### 2.2 Option B: Offline Python Wheels Archive
```bash
# Download locked dependencies as binary wheels
mkdir -p offline_wheels
pip download -r deployment/requirements-lock.txt -d offline_wheels/
tar -czf offline_wheels.tar.gz offline_wheels/
```

Transfer the tarball archive to the air-gapped environment via approved physical media (e.g. write-once optical media or scanned USB).

---

## 3. Air-Gapped Installation (Offline Enclave)

On the secure air-gapped host:

```bash
# 1. Verify transfer integrity
sha256sum -c aegistrace_airgap_image.tar.sha256

# 2. Load the Docker image into the local Docker daemon
docker load -i aegistrace_airgap_image.tar

# 3. Launch the container locally
docker run -d \
  --name aegistrace-airgap \
  -p 8000:8000 \
  -v /var/aegistrace/data:/app/data \
  -v /var/aegistrace/artifacts:/app/artifacts \
  --network none \
  aegistrace:airgap-release
```
Note the `--network none` flag: AegisTrace will run with zero network access interfaces beyond host localhost loopback.

---

## 4. Standalone Offline Verification ("AegisTrace Verify")

Judicial examiners or defense auditors can audit evidence without the server running:

1. Open `apps/web/dist/index.html` directly or navigate to `http://localhost:8000` and select **AegisTrace Verify (Zero-Server)**.
2. Drag and drop any sealed `.zip` evidence package or `manifest.json`.
3. The client-side auditor checks:
   - ML-DSA-65 cryptographic signatures
   - RFC 6962 SHA-256 Merkle consistency
   - Content-addressed artifact hashes
   - Chain of custody log sequence
4. Displays instant **PACKAGE VERIFIED** or **VERIFICATION FAILED** audit verdict with full technical telemetry.
