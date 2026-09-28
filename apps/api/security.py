import hashlib
import os
import re
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from apps.api.config import config
from apps.api.errors import (
    APIException,
    ErrorCode,
    TenantBoundaryViolationError,
    InvalidStateError,
    RateLimitedError,
    ReplayDetectedError,
    InvalidInputError,
)
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

class SecurityPrincipal(BaseModel):
    """
    Authenticated security principal context resolved server-side.
    Zero-trust boundary: clients cannot assert or alter their own identity,
    tenant, or role without cryptographic authentication.
    """
    actor_id: str
    tenant_id: str = "default_tenant"
    role: str
    scopes: List[str] = Field(default_factory=list)
    is_authenticated: bool = True

# Alias for backward compatibility with existing codebase
Actor = SecurityPrincipal

# Enterprise Role Hierarchy & Permissions
ROLE_HIERARCHY: Dict[str, Set[str]] = {
    "system": {
        "system", "administrator", "investigator", "operator",
        "viewer", "recipient", "device", "service_account",
        "authority", "auditor"
    },
    "administrator": {
        "administrator", "operator", "viewer", "investigator",
        "authority", "auditor"
    },
    "investigator": {
        "investigator", "viewer", "auditor"
    },
    "operator": {
        "operator", "viewer"
    },
    "viewer": {
        "viewer"
    },
    "recipient": {
        "recipient"
    },
    "device": {
        "device"
    },
    "service_account": {
        "service_account", "operator", "viewer"
    },
    # Backward compatibility roles
    "authority": {
        "authority", "administrator", "operator", "viewer"
    },
    "auditor": {
        "auditor", "investigator", "viewer"
    },
}

def has_role_permission(principal_role: str, required_role: str) -> bool:
    """Evaluates role hierarchy to determine if principal satisfies required role."""
    effective_roles = ROLE_HIERARCHY.get(principal_role, {principal_role})
    return required_role in effective_roles or "system" in effective_roles

# --- Input Validation & Integrity Defense ---

ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,128}$")
HEX_HASH_REGEX = re.compile(r"^[a-fA-F0-9]{64}$")

def validate_id_format(identifier: str, field_name: str = "identifier") -> str:
    """
    Validates identifier syntax preventing path traversal, control chars, and injection.
    """
    if not identifier or not isinstance(identifier, str):
        raise InvalidInputError(f"Field '{field_name}' must be a non-empty string.")
    clean = identifier.strip()
    if ".." in clean or "/" in clean or "\\" in clean or "\x00" in clean:
        raise APIException(
            code=ErrorCode.FORBIDDEN,
            message=f"Path traversal or prohibited characters detected in {field_name}.",
            status_code=status.HTTP_403_FORBIDDEN
        )
    if not ID_REGEX.match(clean):
        raise InvalidInputError(f"Field '{field_name}' contains invalid characters or exceeds 128 characters.")
    return clean

def validate_hash_hex(hash_str: str, field_name: str = "hash") -> str:
    """
    Validates SHA-256 hexadecimal hash string.
    """
    if not hash_str or not isinstance(hash_str, str):
        raise InvalidInputError(f"Field '{field_name}' must be a valid 64-character hex hash.")
    clean = hash_str.strip()
    if not HEX_HASH_REGEX.match(clean):
        raise InvalidInputError(f"Field '{field_name}' is not a valid 64-character SHA-256 hex string.")
    return clean.lower()

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
    Sniff MIME type from raw magic bytes and container structure to prevent Content-Type spoofing.
    """
    if len(data) == 0:
        return "application/octet-stream"
    try:
        from core.formats.detector import FormatDetector
        res = FormatDetector.identify_format(data)
        return res.mime_type
    except Exception:
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
    Validates uploaded file size, magic-byte MIME type, and checks for polyglot/executable hazards.
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

    # Polyglot & Executable Hazards Check
    # Reject Windows PE executables (MZ), Linux ELF executables, shell scripts, or raw script payloads
    if payload.startswith(b"MZ") or payload.startswith(b"\x7fELF") or payload.startswith(b"#!"):
        raise APIException(
            code=ErrorCode.UNSUPPORTED_ARTIFACT_TYPE,
            message="Executable binary or script payload rejected by zero-trust security policy.",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
    
    # Check for embedded script injections in documents
    lower_sample = payload[:4096].lower()
    if b"<script" in lower_sample or b"javascript:" in lower_sample:
        raise APIException(
            code=ErrorCode.UNSUPPORTED_ARTIFACT_TYPE,
            message="Embedded active script content rejected in document upload.",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )

    # Disallow executable / prohibited media types using safe_mime_check
    is_safe, detected_mime = safe_mime_check(payload, config.allowed_mime_types)
    if not is_safe:
        raise APIException(
            code=ErrorCode.UNSUPPORTED_ARTIFACT_TYPE,
            message=f"Payload rejected: detected unsupported or prohibited media type '{detected_mime}'.",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            details={"detected_mime": detected_mime, "allowed": config.allowed_mime_types}
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

# --- Sliding-Window Rate Limiting Engine ---

class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter.
    Tracks request timestamps per subject key (IP or Principal ID).
    Uses collections.deque for O(1) amortized sliding-window eviction.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._buckets: Dict[str, deque] = {}

    def is_allowed(self, key: str, max_requests: int, window_seconds: float = 60.0) -> Tuple[bool, int]:
        now = time.time()
        with self._lock:
            timestamps = self._buckets.setdefault(key, deque())
            cutoff = now - window_seconds
            # Purge timestamps outside current window in O(1) amortized
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            
            if len(timestamps) >= max_requests:
                oldest = timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                return False, retry_after
            
            timestamps.append(now)
            return True, 0

    def reset(self):
        with self._lock:
            self._buckets.clear()

default_rate_limiter = SlidingWindowRateLimiter()

# --- Anti-Replay Nonce Cache ---

class ReplayProtectionCache:
    """
    Thread-safe anti-replay cache enforcing freshness and single-use semantics
    for signed provenance events and sensitive cryptographic operations.
    """
    def __init__(self, window_seconds: int = 300):
        self._lock = threading.Lock()
        self._seen_nonces: Dict[str, float] = {}
        self.window_seconds = window_seconds
        self._last_prune = 0.0

    def check_and_record(self, nonce: str, timestamp_epoch: Optional[float] = None) -> bool:
        now = time.time()
        with self._lock:
            # Batch prune expired nonces periodically for high throughput
            if now - self._last_prune > 1.0:
                cutoff = now - self.window_seconds
                expired = [n for n, t in self._seen_nonces.items() if t < cutoff]
                for n in expired:
                    del self._seen_nonces[n]
                self._last_prune = now

            # Skew validation
            if timestamp_epoch is not None:
                if abs(now - timestamp_epoch) > self.window_seconds:
                    return False  # Timestamp is too old or too far in future

            if nonce in self._seen_nonces:
                return False  # Replay detected
            
            self._seen_nonces[nonce] = now
            return True

    def reset(self):
        with self._lock:
            self._seen_nonces.clear()

default_replay_cache = ReplayProtectionCache(window_seconds=config.replay_window_seconds)

# --- Authentication & Zero-Trust Resolution ---

def get_current_actor(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_role: Optional[str] = Header(None, alias="X-API-Role"),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-ID"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> SecurityPrincipal:
    """
    Resolves authenticated SecurityPrincipal context server-side.
    Under Zero-Trust, unauthenticated headers cannot grant privileges when auth is enforced.
    """
    # 1. Bearer Token Resolution
    if authorization:
        token = authorization.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        
        if token in config.local_auth_tokens:
            info = config.local_auth_tokens[token]
            return SecurityPrincipal(
                actor_id=info["actor_id"],
                tenant_id=info.get("tenant_id", "default_tenant"),
                role=info["role"],
                scopes=info.get("scopes", []),
                is_authenticated=True
            )
        
        raise APIException(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid bearer token: unrecognized Bearer token provided.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # 2. Header-based Fallback (allowed in prototype/dev mode when enforce_auth is False)
    if x_api_role and not config.enforce_auth:
        role = x_api_role.lower()
        if role not in config.valid_roles:
            raise APIException(
                code=ErrorCode.FORBIDDEN,
                message=f"Invalid role '{x_api_role}'. Must be one of: {', '.join(config.valid_roles)}.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        actor_id = x_actor_id or f"actor_{role}"
        tenant_id = x_tenant_id or "default_tenant"
        return SecurityPrincipal(
            actor_id=actor_id,
            tenant_id=tenant_id,
            role=role,
            scopes=["*"],
            is_authenticated=False
        )

    # 3. Enforcement checks
    if config.enforce_auth or config.require_role_header:
        raise APIException(
            code=ErrorCode.UNAUTHORIZED,
            message="Missing required authentication credentials (Bearer token or X-API-Role header).",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # 4. Default unauthenticated system principal for local prototype tests
    return SecurityPrincipal(
        actor_id="default_actor",
        tenant_id="default_tenant",
        role="system",
        scopes=["*"],
        is_authenticated=False
    )

def require_role(allowed_roles: List[str]) -> Callable:
    """
    FastAPI dependency factory enforcing that the authenticated actor possesses an allowed role
    or inherits it through the enterprise role hierarchy.
    """
    def _role_dependency(actor: SecurityPrincipal = Depends(get_current_actor)) -> SecurityPrincipal:
        has_perm = any(has_role_permission(actor.role, role) for role in allowed_roles)
        if not has_perm:
            raise APIException(
                code=ErrorCode.FORBIDDEN,
                message=f"Access denied: endpoint requires one of [{', '.join(allowed_roles)}], but caller role is '{actor.role}'.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        return actor
    return _role_dependency

# --- Tenant Isolation & Resource Ownership (IDOR) Checks ---

def verify_tenant_boundary(resource_tenant_id: str, principal: SecurityPrincipal, resource_type: str = "resource", resource_id: str = "unknown") -> None:
    """
    Enforces strict multi-tenant isolation.
    Superuser 'system' can cross tenant boundaries for global administration.
    All other actors are strictly confined to their own tenant.
    """
    if principal.role != "system" and principal.tenant_id != resource_tenant_id:
        raise TenantBoundaryViolationError(
            resource_type=resource_type,
            resource_id=resource_id,
            principal_tenant=principal.tenant_id,
            resource_tenant=resource_tenant_id
        )

def require_recipient_access(recipient_id: str, actor: SecurityPrincipal) -> None:
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

def require_document_access(document_id: str, actor: SecurityPrincipal) -> None:
    """
    Enforces authorization boundary on master document artifacts.
    Recipients or edge devices cannot access or download pristine master documents.
    """
    allowed = ["administrator", "operator", "investigator", "viewer", "authority", "auditor", "system"]
    if not any(has_role_permission(actor.role, r) for r in allowed):
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
    Validates caller's role boundary header when role checking is enabled.
    Maintained for explicit header security testing.
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
