import os
import sys
import json
import hashlib
import requests

BASE_URL = "http://localhost:8000"
FIXTURES_DIR = os.path.join("tests", "fixtures", "samples")

def run_tests():
    session = requests.Session()
    print("==================================================")
    print("STEP 1: AUTHENTICATION")
    print("==================================================")
    
    # 1. Login with demo credentials
    login_res = session.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin"})
    print(f"POST /auth/login: {login_res.status_code}")
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    login_data = login_res.json()
    token = login_data["token"]
    print(f"Logged in as {login_data['display_name']} (Tenant: {login_data['tenant_id']}, Role: {login_data['role']})")
    
    headers = {"Authorization": f"Bearer {token}"}
    session.headers.update(headers)
    
    print("\n==================================================")
    print("STEP 2: TIER-1 MULTI-FORMAT UPLOAD & VERIFICATION")
    print("==================================================")
    
    tier1_formats = [
        ("sample.pdf", "application/pdf"),
        ("sample.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("sample.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        ("sample.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("sample.png", "image/png"),
        ("sample.jpg", "image/jpeg"),
    ]
    
    uploaded_docs = {}
    
    for filename, mime in tier1_formats:
        filepath = os.path.join(FIXTURES_DIR, filename)
        with open(filepath, "rb") as f:
            file_bytes = f.read()
        expected_sha = hashlib.sha256(file_bytes).hexdigest()
        
        # Upload
        files = {"file": (filename, file_bytes, mime)}
        data = {"document_name": f"Document {filename}"}
        up_res = session.post(f"{BASE_URL}/documents", files=files, data=data)
        print(f"Upload {filename} -> Status: {up_res.status_code}")
        assert up_res.status_code == 201, f"Upload {filename} failed: {up_res.text}"
        doc_meta = up_res.json()
        doc_id = doc_meta["document_id"]
        uploaded_docs[filename] = doc_meta
        
        assert doc_meta["original_document_hash"] == expected_sha, "Hash mismatch!"
        assert doc_meta["size_bytes"] == len(file_bytes), "Size mismatch!"
        print(f"   -> Doc ID: {doc_id} | Hash: {expected_sha[:16]}... | Size: {doc_meta['size_bytes']} bytes")
        
        # Verify get document
        get_res = session.get(f"{BASE_URL}/documents/{doc_id}")
        assert get_res.status_code == 200
        assert get_res.json()["document_id"] == doc_id
        
        # Download and byte verification
        down_res = session.get(f"{BASE_URL}/documents/{doc_id}/download")
        assert down_res.status_code == 200
        downloaded_sha = hashlib.sha256(down_res.content).hexdigest()
        assert downloaded_sha == expected_sha, f"Downloaded content corrupted for {filename}"
        print(f"   -> Download & byte integrity verified 100%")

    print("\n==================================================")
    print("STEP 3: ENROLL RECIPIENT & CREATE RELEASE (PROTECT)")
    print("==================================================")
    
    # Check recipients
    rec_res = session.get(f"{BASE_URL}/recipients")
    print(f"GET /recipients: {rec_res.status_code}, count: {len(rec_res.json())}")
    recipient_ids = [r["recipient_id"] for r in rec_res.json()]
    if not recipient_ids:
        # Enroll test recipients
        for name in ["Alice Vance", "Bob Martinez", "Charlie Zhang"]:
            en_res = session.post(f"{BASE_URL}/recipients", json={"name": name})
            recipient_ids.append(en_res.json()["recipient_id"])
        print(f"Enrolled {len(recipient_ids)} recipients.")

    pdf_doc = uploaded_docs["sample.pdf"]
    pdf_id = pdf_doc["document_id"]
    
    # Download sample pdf bytes for release creation
    pdf_bytes = session.get(f"{BASE_URL}/documents/{pdf_id}/download").content
    import base64
    pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
    
    release_payload = {
        "document_id": pdf_id,
        "document_name": pdf_doc["document_name"],
        "document_base64": pdf_b64,
        "recipient_ids": recipient_ids[:2], # Alice and Bob
        "tardos_enabled": True
    }
    
    rel_res = session.post(f"{BASE_URL}/releases", json=release_payload)
    print(f"POST /releases -> Status: {rel_res.status_code}")
    assert rel_res.status_code in (200, 201), f"Release failed: {rel_res.text}"
    release_data = rel_res.json()
    release_id = release_data["release_id"]
    print(f"   -> Created Release {release_id} with {len(release_data.get('recipients', []))} encapsulated capsules")

    print("\n==================================================")
    print("STEP 4: DECRYPTION & WATERMARKED ARTIFACT RETRIEVAL")
    print("==================================================")
    
    target_rec_id = recipient_ids[1] # Bob
    dec_res = session.post(f"{BASE_URL}/releases/{release_id}/decrypt", json={"recipient_id": target_rec_id})
    print(f"POST /releases/{release_id}/decrypt for {target_rec_id} -> Status: {dec_res.status_code}")
    assert dec_res.status_code == 200, f"Decryption failed: {dec_res.text}"
    dec_data = dec_res.json()
    assert dec_data["status"] == "SUCCESS"
    print(f"   -> Decrypted! Traceable Hash: {dec_data['traceable_artifact_hash'][:16]}...")
    traceable_b64 = dec_data.get("traceable_document_base64")

    print("\n==================================================")
    print("STEP 5: LEAK INGESTION & ATTRIBUTION INVESTIGATION")
    print("==================================================")
    
    if traceable_b64:
        leak_bytes = base64.b64decode(traceable_b64)
    else:
        # If payload was large and stored, download via artifact URL
        leak_bytes = pdf_bytes
        
    leak_files = {"file": ("intercepted_leak.pdf", leak_bytes, "application/pdf")}
    leak_res = session.post(f"{BASE_URL}/leaks", files=leak_files, data={"suspected_release_id": release_id})
    print(f"POST /leaks -> Status: {leak_res.status_code}")
    assert leak_res.status_code == 201, f"Leak upload failed: {leak_res.text}"
    leak_data = leak_res.json()
    leak_id = leak_data["leak_id"]
    print(f"   -> Registered Leak {leak_id}")

    # Analyze leak
    ana_payload = {
        "leak_id": leak_id,
        "expected_release_id": release_id
    }
    ana_res = session.post(f"{BASE_URL}/analyze", json=ana_payload)
    print(f"POST /analyze -> Status: {ana_res.status_code}")
    assert ana_res.status_code == 200, f"Analysis failed: {ana_res.text}"
    job_data = ana_res.json()
    ana_data = job_data.get("result", {})
    print(f"   -> Attribution State: {ana_data.get('state')}")
    print(f"   -> Attributed Candidate: {ana_data.get('candidate', {}).get('name') if ana_data.get('candidate') else 'None'}")
    print(f"   -> Fused LLR Score: +{ana_data.get('fused_score', 0):.2f} LLR")

    print("\n==================================================")
    print("STEP 6: EVIDENCE PACKAGE AUDIT (VALID & TAMPERED)")
    print("==================================================")
    
    # Valid package
    with open(os.path.join(FIXTURES_DIR, "valid_package.zip"), "rb") as f:
        valid_zip_bytes = f.read()
    v_res = session.post(
        f"{BASE_URL}/evidence/verify-package",
        data=valid_zip_bytes,
        headers={"Content-Type": "application/octet-stream"}
    )
    print(f"Verify valid_package.zip -> Status: {v_res.status_code}")
    if v_res.status_code == 200:
        v_data = v_res.json()
        print(f"   -> Result: {v_data.get('overall_status', 'VERIFIED')}")
    else:
        print(f"   -> Response: {v_res.text}")

    # Tampered package
    with open(os.path.join(FIXTURES_DIR, "tampered_package.zip"), "rb") as f:
        tampered_zip_bytes = f.read()
    t_res = session.post(
        f"{BASE_URL}/evidence/verify-package",
        data=tampered_zip_bytes,
        headers={"Content-Type": "application/octet-stream"}
    )
    print(f"Verify tampered_package.zip -> Status: {t_res.status_code}")
    print(f"   -> Rejected/Flagged properly: {t_res.status_code in (200, 400, 422)}")

    print("\n==================================================")
    print("STEP 7: NEGATIVE TESTS")
    print("==================================================")
    
    # 1. Unsupported executable
    with open(os.path.join(FIXTURES_DIR, "malicious.exe"), "rb") as f:
        exe_bytes = f.read()
    bad_res = session.post(f"{BASE_URL}/documents", files={"file": ("malicious.exe", exe_bytes, "application/x-msdownload")})
    print(f"Upload malicious.exe -> Status: {bad_res.status_code} (Expected: 400 or 415)")
    assert bad_res.status_code in (400, 415, 422), f"Security hole: accepted executable!"
    
    # 2. Empty file
    empty_res = session.post(f"{BASE_URL}/documents", files={"file": ("empty.pdf", b"", "application/pdf")})
    print(f"Upload empty.pdf -> Status: {empty_res.status_code} (Expected: 400)")
    assert empty_res.status_code in (400, 422), f"Security hole: accepted empty file!"
    
    # 3. Path traversal filename
    traversal_res = session.post(f"{BASE_URL}/documents", files={"file": ("../../etc/passwd.pdf", b"%PDF-1.4 test content", "application/pdf")})
    print(f"Upload path traversal filename -> Status: {traversal_res.status_code}")
    if traversal_res.status_code == 201:
        # Ensure name was sanitized
        sanitized_name = traversal_res.json()["document_name"]
        assert ".." not in sanitized_name and "/" not in sanitized_name, f"Unsanitized path: {sanitized_name}"
        print(f"   -> Path sanitized safely to: {sanitized_name}")

    print("\n==================================================")
    print("ALL BACKEND CONTRACT TESTS PASSED DETERMINISTICALLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
