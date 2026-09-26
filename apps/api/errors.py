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

def register_error_handlers(app: FastAPI):
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
        return JSONResponse(status_code=exc.status_code, content=error_payload.model_dump())

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:8]}")
        # Log error safely without exposing raw internal stack to client
        error_payload = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_ERROR,
                message="An internal server error occurred while processing the request.",
                details={"error_class": exc.__class__.__name__},
                request_id=req_id
            )
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_payload.model_dump())
