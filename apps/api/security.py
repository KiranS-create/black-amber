import os
import re
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from apps.api.config import config
from apps.api.errors import APIException, ErrorCode
from security.defense import (
    validate_base64_payload,
    sanitize_header_value,
    sanitize_numeric_bounds,
    sanitize_log_likelihood,
    sanitize_evidence_observation,
    check_evidence_contradiction,
    verify_caller_signature,
    safe_mime_check,
)

class Actor(BaseModel):
    actor_id: str
    role: str

def sanitize_path(filename: str, base_dir: Path) -> Path:
    """
    Sanitize and resolve filename against base_dir, strictly preventing path traversal.
    """
    clean_name = os.path.basename(filename)
    # Remove any dangerous characters, keep only alphanumerics, hyphens, underscores, dots
    clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", clean_name)
    resolved = (base_dir / clean_name).resolve()
    base_resolved = base_dir.resolve()
    
    if not str(resolved).startswith(str(base_resolved)):
        raise APIException(
            code=ErrorCode.FORBIDDEN,
            message="Path traversal detected in requested filename.",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return resolved

def sniff_mime_type(data: bytes) -> str:
    """
    Sniff MIME type from raw magic bytes to prevent Content-Type spoofing.
    """
    if len(data) == 0:
        return "application/octet-stream"
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return "application/octet-stream"

def validate_uploaded_payload(
    payload: bytes,
    declared_content_type: Optional[str] = None,
    max_size: Optional[int] = None
) -> str:
    """
    Validates uploaded file size and magic-byte MIME type.
    Returns the verified MIME type.
    """
    effective_max = max_size if max_size is not None else config.max_upload_size_bytes
    if len(payload) == 0:
        raise APIException(
            code=ErrorCode.INVALID_ANALYSIS_REQUEST,
            message="Uploaded payload is empty (0 bytes).",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    if len(payload) > effective_max:
        raise APIException(
            code=ErrorCode.PAYLOAD_TOO_LARGE,
            message=f"Payload size ({len(payload)} bytes) exceeds maximum allowable limit ({effective_max} bytes).",
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            details={"max_size_bytes": effective_max, "actual_size_bytes": len(payload)}
        )

    sniffed = sniff_mime_type(payload)
    if sniffed not in config.allowed_mime_types and sniffed != "application/octet-stream":
        raise APIException(
            code=ErrorCode.UNSUPPORTED_ARTIFACT_TYPE,
            message=f"MIME type '{sniffed}' is not supported.",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            details={"detected_mime": sniffed, "allowed": config.allowed_mime_types}
        )
    
    return sniffed

def get_current_actor(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_role: Optional[str] = Header(None, alias="X-API-Role"),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-ID")
) -> Actor:
    """
    Resolves the authenticated Actor from Bearer token or role header.
    """
    # 1. Bearer Token Resolution
    if authorization:
        token = authorization.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        
        if token in config.local_auth_tokens:
            info = config.local_auth_tokens[token]
            return Actor(actor_id=info["actor_id"], role=info["role"])
        
        if config.enforce_auth:
            raise APIException(
                code=ErrorCode.UNAUTHORIZED,
                message="Invalid bearer token provided.",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

    # 2. Header-based Fallback (X-API-Role / X-Actor-ID)
    if x_api_role:
        role = x_api_role.lower()
        if role not in config.valid_roles:
            raise APIException(
                code=ErrorCode.FORBIDDEN,
                message=f"Invalid role '{x_api_role}'. Must be one of: {', '.join(config.valid_roles)}.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        actor_id = x_actor_id or f"actor_{role}"
        return Actor(actor_id=actor_id, role=role)

    # 3. Default / Anonymous
    if config.enforce_auth or config.require_role_header:
        raise APIException(
            code=ErrorCode.UNAUTHORIZED,
            message="Missing required authentication credentials (Bearer token or X-API-Role header).",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    return Actor(actor_id="default_actor", role="system")

def require_role(allowed_roles: List[str]) -> Callable:
    """
    FastAPI dependency factory enforcing that the authenticated actor possesses an allowed role.
    """
    def _role_dependency(actor: Actor = Depends(get_current_actor)) -> Actor:
        if actor.role not in allowed_roles and actor.role != "system":
            raise APIException(
                code=ErrorCode.FORBIDDEN,
                message=f"Access denied: endpoint requires one of [{', '.join(allowed_roles)}], but caller is '{actor.role}'.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        return actor
    return _role_dependency

def require_recipient_access(recipient_id: str, actor: Actor) -> None:
    """
    Enforces authorization boundary preventing Insecure Direct Object Reference (IDOR).
    A recipient may ONLY access their own recipient-scoped packages and decryption endpoints.
    """
    if actor.role == "recipient" and actor.actor_id != recipient_id:
        raise APIException(
            code=ErrorCode.FORBIDDEN,
            message=f"Access denied: recipient '{actor.actor_id}' cannot access resources belonging to '{recipient_id}'.",
            status_code=status.HTTP_403_FORBIDDEN
        )

def require_document_access(document_id: str, actor: Actor) -> None:
    """
    Enforces authorization boundary on master document artifacts.
    """
    if actor.role not in ["authority", "auditor", "system"]:
        raise APIException(
            code=ErrorCode.FORBIDDEN,
            message=f"Access denied: role '{actor.role}' is not authorized to access master document '{document_id}'.",
            status_code=status.HTTP_403_FORBIDDEN
        )

def verify_role_boundary(
    required_role: str,
    x_api_role: Optional[str] = Header(None, alias="X-API-Role")
):
    """
    Validates the caller's role boundary header when role checking is enabled.
    """
    if not config.require_role_header:
        return
    
    if not x_api_role:
        raise APIException(
            code=ErrorCode.UNAUTHORIZED,
            message="Missing required 'X-API-Role' authorization header.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    role = x_api_role.lower()
    if role not in config.valid_roles:
        raise APIException(
            code=ErrorCode.FORBIDDEN,
            message=f"Invalid role '{x_api_role}'. Must be one of: {', '.join(config.valid_roles)}.",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    if role != required_role and role != "system":
        raise APIException(
            code=ErrorCode.FORBIDDEN,
            message=f"Access denied: endpoint requires role '{required_role}', but caller holds '{role}'.",
            status_code=status.HTTP_403_FORBIDDEN
        )
