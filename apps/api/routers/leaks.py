from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from apps.api.models import LeakMetadata
from apps.api.orchestrator import default_orchestrator
from apps.api.security import (
    SecurityPrincipal,
    require_role,
    sanitize_header_value,
    validate_id_format,
    validate_uploaded_payload,
    verify_tenant_boundary,
)

router = APIRouter(prefix="/leaks", tags=["Leaks"])

@router.post("", response_model=LeakMetadata, status_code=status.HTTP_201_CREATED)
async def upload_leak(
    file: UploadFile = File(..., description="Leaked document/image binary payload"),
    suspected_document_id: Optional[str] = Form(None, description="Suspected master document ID"),
    suspected_release_id: Optional[str] = Form(None, description="Suspected release ID"),
    actor: SecurityPrincipal = Depends(require_role(["investigator", "administrator", "operator", "authority", "auditor", "system"]))
):
    """
    Ingest intercepted or leaked artifact into Data Plane storage.
    Indexes content under LEAK_ARTIFACT_HASH to preserve cryptographic identity.
    Enforces tenant boundaries, MIME magic checks, and polyglot detection.
    """
    if suspected_document_id:
        validate_id_format(suspected_document_id, "suspected_document_id")
    if suspected_release_id:
        validate_id_format(suspected_release_id, "suspected_release_id")

    content = await file.read()
    sniffed_mime = validate_uploaded_payload(content, file.content_type, filename=file.filename)

    meta = default_orchestrator.ingest_leak(
        leak_bytes=content,
        mime_type=sniffed_mime,
        suspected_document_id=suspected_document_id,
        suspected_release_id=suspected_release_id,
        tenant_id=actor.tenant_id
    )
    return meta

@router.get("", response_model=List[LeakMetadata])
def list_leaks(
    actor: SecurityPrincipal = Depends(require_role(["investigator", "administrator", "viewer", "operator", "authority", "auditor", "system"]))
):
    """List all ingested leak artifacts scoped to tenant."""
    tenant = None if actor.role == "system" else actor.tenant_id
    return default_orchestrator.metadata_repo.list_leaks(tenant_id=tenant)

@router.get("/{leak_id}", response_model=LeakMetadata)
def get_leak(
    leak_id: str,
    actor: SecurityPrincipal = Depends(require_role(["investigator", "administrator", "viewer", "authority", "auditor", "system"]))
):
    """Get metadata for an ingested leak artifact, enforcing tenant isolation."""
    validate_id_format(leak_id, "leak_id")
    leak = default_orchestrator.get_leak(leak_id)
    verify_tenant_boundary(leak.tenant_id, actor, "leak", leak_id)
    return leak

@router.get("/{leak_id}/download")
def download_leak(
    leak_id: str,
    actor: SecurityPrincipal = Depends(require_role(["investigator", "administrator", "operator", "authority", "auditor", "system"]))
):
    """Download raw leak bytes from Data Plane storage."""
    validate_id_format(leak_id, "leak_id")
    leak = default_orchestrator.get_leak(leak_id)
    verify_tenant_boundary(leak.tenant_id, actor, "leak", leak_id)

    leak_bytes = default_orchestrator.storage.retrieve_artifact_bytes(leak.artifact_id)
    safe_filename = sanitize_header_value(f"{leak.leak_id}.bin")
    return Response(
        content=leak_bytes,
        media_type=leak.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache"
        }
    )
