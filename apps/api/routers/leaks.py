from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from apps.api.models import LeakMetadata
from apps.api.orchestrator import default_orchestrator
from apps.api.security import (
    Actor,
    require_role,
    sanitize_header_value,
    validate_uploaded_payload,
)

router = APIRouter(prefix="/leaks", tags=["Leaks"])

@router.post("", response_model=LeakMetadata, status_code=status.HTTP_201_CREATED)
async def upload_leak(
    file: UploadFile = File(..., description="Leaked document/image binary payload"),
    suspected_document_id: Optional[str] = Form(None, description="Suspected master document ID"),
    suspected_release_id: Optional[str] = Form(None, description="Suspected release ID"),
    actor: Actor = Depends(require_role(["authority", "auditor", "system"]))
):
    """
    Ingest intercepted or leaked artifact into Data Plane storage.
    Indexes content under LEAK_ARTIFACT_HASH to preserve cryptographic identity.
    Requires 'authority', 'auditor', or 'system' role.
    """
    content = await file.read()
    sniffed_mime = validate_uploaded_payload(content, file.content_type)

    meta = default_orchestrator.ingest_leak(
        leak_bytes=content,
        mime_type=sniffed_mime,
        suspected_document_id=suspected_document_id,
        suspected_release_id=suspected_release_id
    )
    return meta

@router.get("/{leak_id}", response_model=LeakMetadata)
def get_leak(
    leak_id: str,
    actor: Actor = Depends(require_role(["authority", "auditor", "system"]))
):
    """Get metadata for an ingested leak artifact."""
    return default_orchestrator.get_leak(leak_id)

@router.get("/{leak_id}/download")
def download_leak(
    leak_id: str,
    actor: Actor = Depends(require_role(["authority", "auditor", "system"]))
):
    """Download raw leak bytes from Data Plane storage."""
    leak = default_orchestrator.get_leak(leak_id)
    leak_bytes = default_orchestrator.storage.retrieve_artifact_bytes(leak.artifact_id)
    safe_filename = sanitize_header_value(f"{leak.leak_id}.bin")
    return Response(
        content=leak_bytes,
        media_type=leak.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )
