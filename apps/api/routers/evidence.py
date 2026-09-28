from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Request, status

from apps.api.orchestrator import default_orchestrator
from apps.api.security import (
    APIException,
    ErrorCode,
    SecurityPrincipal,
    get_current_actor,
    require_recipient_access,
    require_role,
    validate_id_format,
    validate_uploaded_payload,
    verify_tenant_boundary,
)
from core.ledger.ledger import EvidenceEvent

router = APIRouter(prefix="/evidence", tags=["Evidence & Audit"])

@router.get("/{release_id}", response_model=List[EvidenceEvent])
def get_release_evidence(
    release_id: str,
    actor: SecurityPrincipal = Depends(require_role(["investigator", "administrator", "viewer", "authority", "auditor", "system"]))
):
    """
    Retrieve all immutable, cryptographically signed decryption provenance events
    recorded in the tamper-evident ledger for a given release.
    Enforces tenant isolation.
    """
    validate_id_format(release_id, "release_id")
    rel = default_orchestrator.get_release(release_id)
    verify_tenant_boundary(getattr(rel, "tenant_id", "default_tenant"), actor, "release", release_id)

    return default_orchestrator.get_release_evidence(release_id)

@router.post("/decryption-events", status_code=status.HTTP_201_CREATED)
def submit_decryption_event(
    event: EvidenceEvent,
    actor: SecurityPrincipal = Depends(get_current_actor)
):
    """
    Decentralized Decryption Event Ingestion:
    Submits a client-signed EvidenceEvent. The server cryptographically verifies the
    ML-DSA-65 post-quantum signature against the recipient's enrolled public identity
    before appending the event to the tamper-evident ledger.
    Enforces anti-replay, IDOR, and tenant boundaries.
    """
    validate_id_format(event.recipient_id, "recipient_id")
    validate_id_format(event.release_id, "release_id")
    validate_id_format(event.event_id, "event_id")
    require_recipient_access(event.recipient_id, actor)

    rel = default_orchestrator.get_release(event.release_id)
    verify_tenant_boundary(getattr(rel, "tenant_id", "default_tenant"), actor, "release", event.release_id)

    event_hash = default_orchestrator.submit_decryption_event(event)
    return {
        "status": "SUCCESS",
        "event_id": event.event_id,
        "event_hash": event_hash,
        "release_id": event.release_id,
        "recipient_id": event.recipient_id
    }


@router.post("/verify-package")
async def verify_evidence_package(
    request: Request,
    tenant_id: Optional[str] = None
):
    """
    Independent Offline Evidence Package Verifier Endpoint:
    Accepts an uploaded evidence package (.zip archive) and verifies:
    1. Manifest ML-DSA-65 post-quantum digital signature.
    2. Merkle tree commitment (RFC-6962 compliant).
    3. Content-addressed SHA-256 object hashes.
    4. Dependency DAG acyclicity and groundings.
    5. Append-only chain of custody continuity.
    6. Historical key bound temporal invariants.
    """
    import tempfile
    from pathlib import Path
    from core.evidence_package.exporter import EvidencePackageExporter
    from core.evidence_package.verifier import OfflineEvidenceVerifier

    package_file = await request.body()
    validate_uploaded_payload(package_file)

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(package_file)
        tmp_path = Path(tmp.name)

    from datetime import datetime, timezone

    try:
        package = EvidencePackageExporter.load_from_zip(tmp_path)
        verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)
        result = verifier.verify_package(
            manifest=package.manifest,
            signature=package.signature,
            objects=package.objects,
            edges=package.edges,
            custody_chain=package.custody_chain,
        )
        return result.model_dump(mode="json")
    except Exception as exc:
        raise APIException(
            code=ErrorCode.INVALID_INPUT,
            message=f"Package corruption or tamper detected: {str(exc)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    finally:
        try:
            tmp_path.unlink()
        except Exception:
            pass
