import hashlib
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.config import config
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import generate_symmetric_key, encrypt_aes_gcm, decrypt_aes_gcm

def run_health_check() -> dict:
    print("=" * 60)
    print("SIH26237 DEPLOYMENT READINESS & HEALTH CHECK")
    print("=" * 60)

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "PASS",
        "checks": {}
    }

    # Check 1: Python Runtime
    py_ver = sys.version.split()[0]
    py_ok = sys.version_info >= (3, 9)
    report["checks"]["python_runtime"] = {
        "version": py_ver,
        "status": "PASS" if py_ok else "FAIL",
        "details": f"Python {py_ver} (required: >= 3.9)"
    }
    print(f"[{'PASS' if py_ok else 'FAIL'}] Python Runtime: {py_ver}")

    # Check 2: Core Cryptographic Self-Test (Post-Quantum & Symmetric)
    crypto_ok = False
    kem_meta = MLKEM768.get_metadata()
    dsa_meta = MLDSA65.get_metadata()
    try:
        # Enforce that active providers are genuine production-safe PQC
        if not MLKEM768.is_production_safe():
            raise RuntimeError(f"ML-KEM-768 provider is NOT production-safe: {kem_meta.get('provider')}")
        if not MLDSA65.is_production_safe():
            raise RuntimeError(f"ML-DSA-65 provider is NOT production-safe: {dsa_meta.get('provider')}")

        # KEM
        kem_kp = MLKEM768.generate_keypair()
        encap = MLKEM768.encapsulate(kem_kp.public_key_bytes)
        decap = MLKEM768.decapsulate(kem_kp.private_key_bytes, encap.ciphertext)
        assert encap.shared_secret == decap

        # DSA
        dsa_kp = MLDSA65.generate_keypair()
        sig = MLDSA65.sign(dsa_kp.private_key_bytes, b"HEALTH_CHECK_MSG")
        assert MLDSA65.verify(dsa_kp.public_key_bytes, b"HEALTH_CHECK_MSG", sig) is True

        # AES-GCM
        k = generate_symmetric_key()
        ct = encrypt_aes_gcm(k, b"HEALTH_CHECK_PLAINTEXT")
        pt = decrypt_aes_gcm(k, ct)
        assert pt == b"HEALTH_CHECK_PLAINTEXT"

        crypto_ok = True
    except Exception as e:
        crypto_err = str(e)

    report["checks"]["crypto_primitives"] = {
        "status": "PASS" if crypto_ok else "FAIL",
        "kem_provider": kem_meta.get("provider", "UNKNOWN"),
        "dsa_provider": dsa_meta.get("provider", "UNKNOWN"),
        "is_post_quantum": kem_meta.get("is_post_quantum", False) and dsa_meta.get("is_post_quantum", False),
        "details": f"ML-KEM-768 ({kem_meta.get('provider')}), ML-DSA-65 ({dsa_meta.get('provider')}), AES-256-GCM validated" if crypto_ok else crypto_err
    }
    print(f"[{'PASS' if crypto_ok else 'FAIL'}] Cryptographic Primitives: ML-KEM-768 ({kem_meta.get('provider')}), ML-DSA-65 ({dsa_meta.get('provider')}), AES-256-GCM")


    # Check 3: Storage & Writable Data Plane
    storage_ok = False
    try:
        test_file = config.artifacts_dir / ".health_test.tmp"
        with open(test_file, "w") as f:
            f.write("HEALTH_OK")
        with open(test_file, "r") as f:
            content = f.read()
        test_file.unlink()
        storage_ok = (content == "HEALTH_OK")
    except Exception as e:
        storage_err = str(e)

    report["checks"]["storage_writable"] = {
        "status": "PASS" if storage_ok else "FAIL",
        "path": str(config.artifacts_dir)
    }
    print(f"[{'PASS' if storage_ok else 'FAIL'}] Artifact Storage Writable: {config.artifacts_dir}")

    # Check 4: FastAPI In-Process API Endpoint Response
    api_ok = False
    try:
        client = TestClient(app)
        h_res = client.get("/health")
        c_res = client.get("/capabilities")
        l_res = client.get("/ledger/verify")
        if h_res.status_code == 200 and c_res.status_code == 200 and l_res.status_code == 200:
            api_ok = True
            report["checks"]["api_endpoints"] = {
                "status": "PASS",
                "health_response": h_res.json(),
                "ledger_valid": l_res.json()["is_valid"]
            }
        else:
            report["checks"]["api_endpoints"] = {"status": "FAIL", "code": h_res.status_code}
    except Exception as e:
        report["checks"]["api_endpoints"] = {"status": "FAIL", "error": str(e)}

    print(f"[{'PASS' if api_ok else 'FAIL'}] REST API & Router Health: /health, /capabilities, /ledger/verify")

    # Check 5: Web Frontend Production Build
    dist_index = PROJECT_ROOT / "apps" / "web" / "dist" / "index.html"
    fe_ok = dist_index.exists()
    report["checks"]["frontend_build"] = {
        "status": "PASS" if fe_ok else "WARN",
        "details": "Production distribution present" if fe_ok else "apps/web/dist not found (run 'npx vite build')"
    }
    print(f"[{'PASS' if fe_ok else 'WARN'}] Web Dashboard Distribution: {dist_index}")

    # Overall Status
    all_passed = py_ok and crypto_ok and storage_ok and api_ok
    report["status"] = "PASS" if all_passed else "FAIL"

    # Save to artifacts/deployment
    out_dir = PROJECT_ROOT / "artifacts" / "deployment"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "health_report.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n[+] Health report written to: {out_file}")
    print("=" * 60)
    print(f"DEPLOYMENT HEALTH VERDICT: {report['status']}")
    print("=" * 60)
    return report

if __name__ == "__main__":
    report = run_health_check()
    if report["status"] != "PASS":
        sys.exit(1)
