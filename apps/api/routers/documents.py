from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from apps.api.models import DocumentListResponse, DocumentMetadata
from apps.api.orchestrator import default_orchestrator
from apps.api.security import (
    SecurityPrincipal,
    get_current_actor,
    require_role,
    require_document_access,
    sanitize_header_value,
    validate_id_format,
    validate_uploaded_payload,
    verify_tenant_boundary,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("", response_model=DocumentMetadata, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="Document binary payload (PDF or image)"),
    document_name: Optional[str] = Form(None, description="Human-readable document title"),
    document_id: Optional[str] = Form(None, description="Optional custom document ID"),
    actor: SecurityPrincipal = Depends(require_role(["operator", "administrator", "authority", "system"]))
):
    """
    Register and store an original document in Data Plane storage.
    Validates size, verifies MIME magic bytes, and indexes under ORIGINAL_DOCUMENT_HASH.
    Scoped to the authenticated principal's tenant.
    """
    if document_id:
        validate_id_format(document_id, "document_id")

    content = await file.read()
    sniffed_mime = validate_uploaded_payload(content, file.content_type)
    doc_name = document_name or file.filename or "Untitled.pdf"

    meta = default_orchestrator.register_document(
        document_bytes=content,
        document_name=doc_name,
        document_id=document_id,
        mime_type=sniffed_mime,
        tenant_id=actor.tenant_id
    )
    return meta

@router.get("", response_model=DocumentListResponse)
def list_documents(
    actor: SecurityPrincipal = Depends(require_role(["operator", "administrator", "investigator", "viewer", "authority", "auditor", "system"]))
):
    """List all registered master documents scoped to tenant."""
    tenant = None if actor.role == "system" else actor.tenant_id
    docs = default_orchestrator.metadata_repo.list_documents(tenant_id=tenant)
    return DocumentListResponse(documents=docs, total=len(docs))

@router.get("/{document_id}", response_model=DocumentMetadata)
def get_document(
    document_id: str,
    actor: SecurityPrincipal = Depends(require_role(["operator", "administrator", "investigator", "viewer", "authority", "auditor", "system"]))
):
    """Get metadata for a specific document, enforcing tenant isolation."""
    validate_id_format(document_id, "document_id")
    doc = default_orchestrator.get_document(document_id)
    verify_tenant_boundary(doc.tenant_id, actor, "document", document_id)
    return doc

@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    actor: SecurityPrincipal = Depends(require_role(["operator", "administrator", "investigator", "viewer", "authority", "auditor", "system"]))
):
    """
    Download pristine master document bytes from Data Plane storage.
    Applies strict Content-Disposition header sanitization to prevent CRLF splitting.
    Enforces tenant boundaries and document access rights.
    """
    validate_id_format(document_id, "document_id")
    require_document_access(document_id, actor)
    doc = default_orchestrator.get_document(document_id)
    verify_tenant_boundary(doc.tenant_id, actor, "document", document_id)

    doc_bytes = default_orchestrator.get_document_bytes(document_id)
    safe_filename = sanitize_header_value(doc.document_name, fallback=f"{doc.document_id}.pdf")

    return Response(
        content=doc_bytes,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache"
        }
    )
