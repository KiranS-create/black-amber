import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

class ErrorCode(str, Enum):
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    RECIPIENT_NOT_FOUND = "RECIPIENT_NOT_FOUND"
    RELEASE_NOT_FOUND = "RELEASE_NOT_FOUND"
    ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
    ARTIFACT_HASH_MISMATCH = "ARTIFACT_HASH_MISMATCH"
    INVALID_RELEASE = "INVALID_RELEASE"
    INVALID_ANALYSIS_REQUEST = "INVALID_ANALYSIS_REQUEST"
    CAPACITY_INSUFFICIENT = "CAPACITY_INSUFFICIENT"
    NO_SIGNAL = "NO_SIGNAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICT = "CONFLICT"
    UNSUPPORTED_ARTIFACT_TYPE = "UNSUPPORTED_ARTIFACT_TYPE"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    TENANT_BOUNDARY_VIOLATION = "TENANT_BOUNDARY_VIOLATION"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    INVALID_STATE = "INVALID_STATE"
    INVALID_INPUT = "INVALID_INPUT"
    RATE_LIMITED = "RATE_LIMITED"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    request_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ErrorResponse(BaseModel):
    error: ErrorDetail

class APIException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class DocumentNotFoundError(APIException):
    def __init__(self, doc_id: str):
        super().__init__(
            code=ErrorCode.DOCUMENT_NOT_FOUND,
            message=f"Document with ID '{doc_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )

class RecipientNotFoundError(APIException):
    def __init__(self, recipient_id: str):
        super().__init__(
            code=ErrorCode.RECIPIENT_NOT_FOUND,
            message=f"Recipient with ID '{recipient_id}' not found in registry.",
            status_code=status.HTTP_404_NOT_FOUND
        )

class ReleaseNotFoundError(APIException):
    def __init__(self, release_id: str):
        super().__init__(
            code=ErrorCode.RELEASE_NOT_FOUND,
            message=f"Release with ID '{release_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )

class ArtifactNotFoundError(APIException):
    def __init__(self, artifact_id: str):
        super().__init__(
            code=ErrorCode.ARTIFACT_NOT_FOUND,
            message=f"Artifact with ID '{artifact_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )

class ArtifactHashMismatchError(APIException):
    def __init__(self, expected: str, actual: str):
        super().__init__(
            code=ErrorCode.ARTIFACT_HASH_MISMATCH,
            message=f"Artifact hash mismatch: expected '{expected}', computed '{actual}'.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"expected_hash": expected, "computed_hash": actual}
        )

class CapacityInsufficientError(APIException):
    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.CAPACITY_INSUFFICIENT,
            message=f"Traceability capacity insufficient: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {}
        )

class TenantBoundaryViolationError(APIException):
    def __init__(self, resource_type: str, resource_id: str, principal_tenant: str, resource_tenant: str):
        super().__init__(
            code=ErrorCode.TENANT_BOUNDARY_VIOLATION,
            message=f"Access denied: {resource_type} '{resource_id}' belongs to tenant '{resource_tenant}', caller is in tenant '{principal_tenant}'.",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"resource_type": resource_type, "resource_id": resource_id, "principal_tenant": principal_tenant}
        )

class IDORViolationError(APIException):
    def __init__(self, message: str = "Access denied: unauthorized access to recipient-scoped resource.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.FORBIDDEN,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details or {}
        )

class InvalidStateError(APIException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.INVALID_STATE,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details or {}
        )

class RateLimitedError(APIException):
    def __init__(self, retry_after: int = 60, details: Optional[Dict[str, Any]] = None):
        d = details or {}
        d["retry_after_seconds"] = retry_after
        super().__init__(
            code=ErrorCode.RATE_LIMITED,
            message=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=d
        )

class ReplayDetectedError(APIException):
    def __init__(self, message: str = "Duplicate request nonce or timestamp replay detected.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.REPLAY_DETECTED,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details or {}
        )

class AuthenticationFailedError(APIException):
    def __init__(self, message: str = "Authentication failed: invalid or missing credentials."):
        super().__init__(
            code=ErrorCode.AUTHENTICATION_FAILED,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationFailedError(APIException):
    def __init__(self, message: str = "Authorization failed: insufficient permissions."):
        super().__init__(
            code=ErrorCode.AUTHORIZATION_FAILED,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )

class InvalidInputError(APIException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.INVALID_INPUT,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {}
        )

def register_error_handlers(app: FastAPI):
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:8]}")
        error_payload = ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=req_id
            )
        )
        headers = {}
        if exc.code == ErrorCode.RATE_LIMITED:
            retry_after = exc.details.get("retry_after_seconds", 60)
            headers["Retry-After"] = str(retry_after)
        return JSONResponse(status_code=exc.status_code, content=error_payload.model_dump(), headers=headers)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:8]}")
        code = ErrorCode.UNAUTHORIZED if exc.status_code == 401 else (
            ErrorCode.FORBIDDEN if exc.status_code == 403 else (
                ErrorCode.RESOURCE_NOT_FOUND if exc.status_code == 404 else (
                    ErrorCode.RATE_LIMITED if exc.status_code == 429 else ErrorCode.INTERNAL_ERROR
                )
            )
        )
        error_payload = ErrorResponse(
            error=ErrorDetail(
                code=code,
                message=str(exc.detail),
                details={"status_code": exc.status_code},
                request_id=req_id
            )
        )
        return JSONResponse(status_code=exc.status_code, content=error_payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:8]}")
        error_payload = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INVALID_INPUT,
                message="Request body or query validation failed.",
                details={"errors": [str(e) for e in exc.errors()]},
                request_id=req_id
            )
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_payload.model_dump())

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:8]}")
        # Log error safely without exposing raw internal stack or paths to client
        error_payload = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_ERROR,
                message="An internal server error occurred while processing the request.",
                details={"error_class": exc.__class__.__name__},
                request_id=req_id
            )
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_payload.model_dump())
