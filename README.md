# SIH26237 — Cryptographic Attribution & Immutable Decryption Provenance

**Smart India Hackathon 2026**
**Project ID:** SIH26237

## Overview
SIH26237 provides a post-quantum cryptographic framework for multi-recipient document distribution, recipient-specific cryptographic traceability, and verifiable post-leak attribution with fail-closed provenance audit chains.

## Key Features
- **Post-Quantum Envelope Encryption**: AES-256-GCM encrypted document with ML-KEM-768 recipient key encapsulation.
- **Recipient Identity & Key Isolation**: Independent keypairs for each recipient; packages contain only recipient-specific cryptographic material.
- **Traceability & Marker Binding**: Recipient copies are embedded with cryptographically authenticated attribution markers.
- **Decryption Provenance**: Decryption operations generate signed provenance events.
- **Tamper-Evident Ledger**: Hash-chained audit ledger preventing retroactive log tampering or event fabrication.
- **Fail-Closed Attribution Engine**: Accusations are only made when cryptographic evidence is completely verified; forged, missing, or altered markers return `ABSTAIN`.

## Quick Start

### 1. Environment Verification
```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_env.ps1
```

### 2. Python Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Run Automated End-to-End Demo
```powershell
python demo/end_to_end.py
```

### 4. Run Pytest Suite
```powershell
pytest -v
```

### 5. Launch API Server
```powershell
uvicorn apps.api.main:app --reload --port 8000
```
