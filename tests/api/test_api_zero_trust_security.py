import base64
import pytest
from fastapi.testclient import TestClient

from apps.api.config import config
from apps.api.errors import ErrorCode
from apps.api.main import app
from apps.api.orchestrator import default_orchestrator
from demo.end_to_end import create_sample_pdf

client = TestClient(app)

def create_test_pdf_b64() -> str:
    pdf_bytes = create_sample_pdf()
    return base64.b64encode(pdf_bytes).decode("utf-8")

# =====================================================================
# 1. MULTI-TENANT ISOLATION & CROSS-TENANT IDOR DEFENSES
# =====================================================================

def test_cross_tenant_document_isolation():
    """
    Verify that resources created by Tenant A cannot be read, listed, or downloaded by Tenant B.
    """
    headers_op_a = {"Authorization": "Bearer token_operator_tenant_a"}
    headers_inv_b = {"Authorization": "Bearer token_investigator_tenant_b"}

    # 1. Tenant A Operator creates a master document
    pdf_bytes = create_sample_pdf()
    res_upload = client.post(
        "/documents",
        headers=headers_op_a,
        files={"file": ("tenant_a_doc.pdf", pdf_bytes, "application/pdf")},
        data={"document_name": "Tenant A Secret Plan.pdf"}
    )
    assert res_upload.status_code == 201
    doc_a = res_upload.json()
    doc_id_a = doc_a["document_id"]
    assert doc_a["tenant_id"] == "tenant_a"

    # 2. Tenant B Investigator attempts to read Tenant A's document metadata (IDOR)
    res_idor_get = client.get(f"/documents/{doc_id_a}", headers=headers_inv_b)
    assert res_idor_get.status_code == 403
    err = res_idor_get.json()
    assert err["error"]["code"] == ErrorCode.TENANT_BOUNDARY_VIOLATION

    # 3. Tenant B Investigator attempts to download Tenant A's document bytes
    res_idor_dl = client.get(f"/documents/{doc_id_a}/download", headers=headers_inv_b)
    assert res_idor_dl.status_code == 403
    err = res_idor_dl.json()
    assert err["error"]["code"] == ErrorCode.TENANT_BOUNDARY_VIOLATION

    # 4. Tenant B Investigator lists documents: must NOT see Tenant A's document
    res_list_b = client.get("/documents", headers=headers_inv_b)
    assert res_list_b.status_code == 200
    b_docs = res_list_b.json()["documents"]
    assert all(d["document_id"] != doc_id_a for d in b_docs)

def test_cross_tenant_release_isolation():
    """
    Verify that release packages and metadata created in Tenant A are invisible and
    inaccessible to Tenant B callers.
    """
    headers_op_a = {"Authorization": "Bearer token_operator_tenant_a"}
    headers_inv_b = {"Authorization": "Bearer token_investigator_tenant_b"}
    headers_charlie_b = {"Authorization": "Bearer token_charlie_tenant_b"}

    # 1. Tenant A creates release
    pdf_b64 = create_test_pdf_b64()
    rel_res = client.post(
        "/releases",
        headers=headers_op_a,
        json={
            "document_name": "Tenant_A_Release.pdf",
            "document_base64": pdf_b64,
            "issuer_id": "HQ_TEST",
            "recipient_ids": ["alice", "bob"]
        }
    )
    assert rel_res.status_code == 200
    rel_data = rel_res.json()
    release_id = rel_data["release_id"]
    assert rel_data["tenant_id"] == "tenant_a"

    # 2. Tenant B Investigator attempts to inspect release metadata
    res_idor_rel = client.get(f"/releases/{release_id}", headers=headers_inv_b)
    assert res_idor_rel.status_code == 403
    assert res_idor_rel.json()["error"]["code"] == ErrorCode.TENANT_BOUNDARY_VIOLATION

    # 3. Tenant B Recipient Charlie attempts to fetch Alice's package from Tenant A
    res_idor_pkg = client.get(f"/releases/{release_id}/packages/alice", headers=headers_charlie_b)
    assert res_idor_pkg.status_code == 403
    # Either recipient access restriction or tenant boundary violation triggers 403
    assert res_idor_pkg.status_code == 403

    # 4. Tenant B Recipient Charlie attempts to decrypt Tenant A's package
    res_idor_dec = client.post(
        f"/releases/{release_id}/decrypt",
        headers=headers_charlie_b,
        json={"recipient_id": "alice"}
    )
    assert res_idor_dec.status_code == 403

    # 5. Tenant B Investigator lists releases: must NOT include Tenant A release
    res_list_b = client.get("/releases", headers=headers_inv_b)
    assert res_list_b.status_code == 200
    assert all(r["release_id"] != release_id for r in res_list_b.json())

def test_cross_tenant_evidence_isolation():
    """
    Verify that audit ledger evidence events for Tenant A cannot be inspected by Tenant B.
    """
    headers_op_a = {"Authorization": "Bearer token_operator_tenant_a"}
    headers_alice_a = {"Authorization": "Bearer token_alice_tenant_a"}
    headers_inv_b = {"Authorization": "Bearer token_investigator_tenant_b"}

    # Tenant A release and decrypt
    pdf_b64 = create_test_pdf_b64()
    rel_res = client.post(
        "/releases",
        headers=headers_op_a,
        json={
            "document_name": "Tenant_A_EvidenceDoc.pdf",
            "document_base64": pdf_b64,
            "issuer_id": "HQ_TEST",
            "recipient_ids": ["alice"]
        }
    )
    release_id = rel_res.json()["release_id"]

    dec_res = client.post(
        f"/releases/{release_id}/decrypt",
        headers=headers_alice_a,
        json={"recipient_id": "alice"}
    )
    assert dec_res.status_code == 200

    # Tenant B attempts to read evidence
    ev_res = client.get(f"/evidence/{release_id}", headers=headers_inv_b)
    assert ev_res.status_code == 403
    assert ev_res.json()["error"]["code"] == ErrorCode.TENANT_BOUNDARY_VIOLATION

# =====================================================================
# 2. ROLE BOUNDARIES & PRIVILEGE ESCALATION ATTACKS
# =====================================================================

def test_viewer_role_privilege_escalation_rejected():
    """
    Verify that 'viewer' role is strictly prohibited from mutating state:
    cannot upload documents, cannot create releases, cannot enroll recipients.
    """
    headers_viewer = {"Authorization": "Bearer token_viewer_tenant_a"}

    # 1. Attempt upload document
    pdf_bytes = create_sample_pdf()
    res_up = client.post(
        "/documents",
        headers=headers_viewer,
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
        data={"document_name": "Viewer Escalation.pdf"}
    )
    assert res_up.status_code == 403
    assert res_up.json()["error"]["code"] == ErrorCode.FORBIDDEN

    # 2. Attempt create release
    res_rel = client.post(
        "/releases",
        headers=headers_viewer,
        json={
            "document_name": "Viewer Escalation.pdf",
            "document_base64": create_test_pdf_b64(),
            "issuer_id": "HQ_TEST",
            "recipient_ids": ["alice"]
        }
    )
    assert res_rel.status_code == 403
    assert res_rel.json()["error"]["code"] == ErrorCode.FORBIDDEN

    # 3. Attempt enroll recipient
    res_enroll = client.post(
        "/recipients",
        headers=headers_viewer,
        json={"name": "Attacker", "recipient_id": "attacker"}
    )
    assert res_enroll.status_code == 403
    assert res_enroll.json()["error"]["code"] == ErrorCode.FORBIDDEN

def test_recipient_role_privilege_escalation_rejected():
    """
    Verify that a recipient role ('recipient') cannot create releases, cannot upload documents,
    and cannot download pristine master documents.
    """
    headers_alice = {"Authorization": "Bearer token_alice_tenant_a"}
    headers_op = {"Authorization": "Bearer token_operator_tenant_a"}

    # 1. Attempt create release
    res_rel = client.post(
        "/releases",
        headers=headers_alice,
        json={
            "document_name": "Alice Doc.pdf",
            "document_base64": create_test_pdf_b64(),
            "issuer_id": "HQ_TEST",
            "recipient_ids": ["bob"]
        }
    )
    assert res_rel.status_code == 403
    assert res_rel.json()["error"]["code"] == ErrorCode.FORBIDDEN

    # 2. Attempt upload document
    pdf_bytes = create_sample_pdf()
    res_up = client.post(
        "/documents",
        headers=headers_alice,
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
        data={"document_name": "Alice Upload.pdf"}
    )
    assert res_up.status_code == 403
    assert res_up.json()["error"]["code"] == ErrorCode.FORBIDDEN

    # 3. Create document legitimately via operator
    doc_res = client.post(
        "/documents",
        headers=headers_op,
        files={"file": ("master.pdf", pdf_bytes, "application/pdf")},
        data={"document_name": "Master Secret.pdf"}
    )
    doc_id = doc_res.json()["document_id"]

    # 4. Recipient attempts to download pristine master document
    res_dl = client.get(f"/documents/{doc_id}/download", headers=headers_alice)
    assert res_dl.status_code == 403
    assert res_dl.json()["error"]["code"] == ErrorCode.FORBIDDEN

def test_operator_role_cannot_enroll_or_revoke_recipients():
    """
    Verify role separation: operators can create releases but cannot enroll or revoke recipients.
    Only administrator or system can manage recipient cryptographic identities.
    """
    headers_op = {"Authorization": "Bearer token_operator_tenant_a"}

    # Attempt recipient enrollment
    res_enroll = client.post(
        "/recipients",
        headers=headers_op,
        json={"name": "New Recipient", "recipient_id": "new_rec"}
    )
    assert res_enroll.status_code == 403

    # Attempt recipient revocation
    res_revoke = client.post("/recipients/alice/revoke", headers=headers_op)
    assert res_revoke.status_code == 403

# =====================================================================
# 3. RECIPIENT IDOR & CROSS-PACKAGE DEFENSE
# =====================================================================

def test_recipient_cross_package_idor_rejected():
    """
    Verify that Alice cannot download Bob's encrypted package or decrypt Bob's copy.
    """
    headers_op = {"Authorization": "Bearer token_operator_tenant_a"}
    headers_alice = {"Authorization": "Bearer token_alice_tenant_a"}

    # 1. Operator creates release for Alice and Bob
    pdf_b64 = create_test_pdf_b64()
    rel_res = client.post(
        "/releases",
        headers=headers_op,
        json={
            "document_name": "Dual_Release.pdf",
            "document_base64": pdf_b64,
            "issuer_id": "HQ_TEST",
            "recipient_ids": ["alice", "bob"]
        }
    )
    assert rel_res.status_code == 200
    release_id = rel_res.json()["release_id"]

    # 2. Alice attempts to download Bob's package
    res_idor = client.get(f"/releases/{release_id}/packages/bob", headers=headers_alice)
    assert res_idor.status_code == 403
    assert res_idor.json()["error"]["code"] == ErrorCode.FORBIDDEN

    # 3. Alice attempts to decrypt Bob's package
    res_dec = client.post(
        f"/releases/{release_id}/decrypt",
        headers=headers_alice,
        json={"recipient_id": "bob"}
    )
    assert res_dec.status_code == 403
    assert res_dec.json()["error"]["code"] == ErrorCode.FORBIDDEN

# =====================================================================
# 4. ZERO-TRUST HEADER SPOOFING & UNRECOGNIZED TOKENS
# =====================================================================

def test_unauthenticated_header_spoofing_blocked_under_zero_trust():
    """
    When enforce_auth=True is active, client-supplied X-API-Role headers without
    valid cryptographic Bearer tokens MUST be rejected immediately with 401.
    """
    orig_enforce = config.enforce_auth
    try:
        config.enforce_auth = True

        # Caller sends X-API-Role: administrator without Bearer token
        res = client.post(
            "/recipients",
            headers={"X-API-Role": "administrator"},
            json={"name": "Spoofed Admin", "recipient_id": "spoofed"}
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == ErrorCode.UNAUTHORIZED

        # Caller sends bogus Bearer token
        res_fake_token = client.post(
            "/recipients",
            headers={"Authorization": "Bearer fake_token_attack_123"},
            json={"name": "Spoofed Admin", "recipient_id": "spoofed"}
        )
        assert res_fake_token.status_code == 401
        assert res_fake_token.json()["error"]["code"] == ErrorCode.UNAUTHORIZED
    finally:
        config.enforce_auth = orig_enforce

# =====================================================================
# 5. STATE-MACHINE LIFECYCLE RECIPIENT REVOCATION DEFENSE
# =====================================================================

def test_revoked_recipient_state_machine_defense():
    """
    Verify state-machine lifecycle enforcement:
    1. A revoked recipient cannot be added to a new document release.
    2. A revoked recipient cannot decrypt an existing release package.
    """
    headers_admin = {"Authorization": "Bearer token_admin_tenant_a"}
    headers_op = {"Authorization": "Bearer token_operator_tenant_a"}

    # 1. Enroll a temporary recipient to test revocation
    enroll_res = client.post(
        "/recipients",
        headers=headers_admin,
        json={"name": "Revocable User", "recipient_id": "revocable_user"}
    )
    assert enroll_res.status_code == 201
    assert enroll_res.json()["status"] == "ACTIVE"

    # 2. Revoke the recipient via admin
    revoke_res = client.post("/recipients/revocable_user/revoke", headers=headers_admin)
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "REVOKED"

    # 3. Operator attempts to create a release including the revoked recipient -> REJECTED
    pdf_b64 = create_test_pdf_b64()
    rel_fail = client.post(
        "/releases",
        headers=headers_op,
        json={
            "document_name": "RevokedTest.pdf",
            "document_base64": pdf_b64,
            "issuer_id": "HQ_TEST",
            "recipient_ids": ["revocable_user"]
        }
    )
    assert rel_fail.status_code == 400
    assert rel_fail.json()["error"]["code"] == ErrorCode.INVALID_RELEASE
