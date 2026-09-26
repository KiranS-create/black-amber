import base64
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Python 3.9 typing compatibility: flatten nested Literal types for pydantic OpenAPI schema generation
try:
    import pydantic.json_schema as _pjs
    _orig_get_literal_values = _pjs.get_literal_values
    def _patched_get_literal_values(annotation, *args, **kwargs):
        for val in _orig_get_literal_values(annotation, *args, **kwargs):
            if hasattr(val, "__args__"):
                yield from _patched_get_literal_values(val, *args, **kwargs)
            else:
                yield val
    _pjs.get_literal_values = _patched_get_literal_values
    import typing_inspection
    typing_inspection.get_literal_values = _patched_get_literal_values
except Exception:
    pass

from apps.api.config import config
from apps.api.errors import register_error_handlers, APIException, ErrorCode
from apps.api.orchestrator import default_orchestrator
from apps.api.routers import (
    analysis,
    documents,
    evidence,
    leaks,
    recipients,
    releases,
    system,
)
from core.recipient import default_registry
from core.release import default_release_manager
from core.provenance.decryption import default_decryption_client
from core.ledger.ledger import default_ledger
from core.attribution.engine import AttributionResult, default_attribution_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure demo recipients and initial storage
    default_registry.init_demo_recipients()
    yield
    # Shutdown

app = FastAPI(
    title=config.title,
    version=config.version,
    description=config.description,
    lifespan=lifespan
)

# Request ID & Logging Middleware
@app.middleware("http")
async def correlation_and_audit_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:10]}"
    request.state.request_id = req_id
    start_time = time.perf_counter()

    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
    return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register uniform error handlers
register_error_handlers(app)

# Mount Modular Routers
app.include_router(system.router)
app.include_router(documents.router)
app.include_router(recipients.router)
app.include_router(releases.router)
app.include_router(leaks.router)
app.include_router(analysis.router)
app.include_router(evidence.router)

# -------------------------------------------------------------
# Backward-Compatibility Routes (v0.1 Contract Support)
# -------------------------------------------------------------
class LegacyAnalyzeLeakRequest(BaseModel):
    leaked_document_base64: str
    release_id: Optional[str] = None

@app.post(
    "/leaks/analyze",
    response_model=AttributionResult,
    tags=["Attribution (Legacy)"],
    summary="Legacy leak analysis endpoint (backward compatible)"
)
def legacy_analyze_leak(req: LegacyAnalyzeLeakRequest):
    """
    Direct synchronous leak analysis returning raw AttributionResult
    for backward compatibility with v0.1 API clients.
    """
    from apps.api.security import validate_base64_payload
    try:
        leaked_bytes = validate_base64_payload(
            req.leaked_document_base64,
            max_size_bytes=config.max_upload_size_bytes
        )
    except Exception as e:
        raise APIException(
            code=ErrorCode.INVALID_ANALYSIS_REQUEST,
            message=f"Invalid or oversized base64 payload for leaked document: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    result = default_attribution_engine.analyze_leak(
        leaked_document_bytes=leaked_bytes,
        expected_release_id=req.release_id
    )
    return result
