import base64
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
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
    auth,
    directory,
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

from apps.api.security import default_rate_limiter, get_current_actor
from apps.api.errors import ErrorDetail, ErrorResponse, RateLimitedError

# Request ID & Audit Logging Middleware
@app.middleware("http")
async def correlation_and_audit_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:10]}"
    request.state.request_id = req_id
    start_time = time.perf_counter()

    # Rate Limiting Guard
    if config.rate_limit_enabled and request.url.path not in ["/health", "/docs", "/openapi.json", "/redoc"]:
        client_ip = request.client.host if request.client else "127.0.0.1"
        auth_header = request.headers.get("Authorization", "")
        # Resolve limit tier based on endpoint sensitivity
        path = request.url.path
        if path in ["/analyze", "/leaks/analyze", "/releases", "/ledger/verify"]:
            max_limit = config.rate_limit_crypto
            tier = "crypto"
        elif path in ["/documents", "/leaks"] and request.method == "POST":
            max_limit = config.rate_limit_upload
            tier = "upload"
        else:
            max_limit = config.rate_limit_default
            tier = "default"

        rate_key = f"{client_ip}:{auth_header}:{tier}"
        allowed, retry_after = default_rate_limiter.is_allowed(
            rate_key,
            max_requests=max_limit,
            window_seconds=config.rate_limit_window_seconds
        )
        if not allowed:
            from fastapi.responses import JSONResponse
            err_resp = ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.RATE_LIMITED,
                    message=f"Rate limit exceeded for tier '{tier}'. Retry after {retry_after} seconds.",
                    details={"tier": tier, "limit": max_limit, "retry_after_seconds": retry_after},
                    request_id=req_id
                )
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=err_resp.model_dump(),
                headers={"Retry-After": str(retry_after), "X-Request-ID": req_id}
            )

    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    # Production Security Response Headers (Defense in Depth)
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob:; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "connect-src 'self' https: http:;"
    )

    # Enforce no-store on sensitive artifact downloads, packages, and decryption responses
    if any(k in request.url.path for k in ["/download", "/packages", "/decrypt", "/provenance"]):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"

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
app.include_router(auth.router)
app.include_router(system.router)
app.include_router(directory.router)
app.include_router(documents.router)
app.include_router(recipients.router)
app.include_router(releases.router)
app.include_router(leaks.router)
app.include_router(analysis.router)
app.include_router(evidence.router)

# -------------------------------------------------------------
# Static Single Page Application (SPA) Serving for Production
# -------------------------------------------------------------
dist_path = config.base_dir / "apps" / "web" / "dist"
if dist_path.exists():
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    assets_path = dist_path / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="static_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Do not catch API or documentation routes
        api_prefixes = (
            "api", "docs", "openapi.json", "health", "ready", "capabilities",
            "auth", "documents", "releases", "recipients", "leaks", "analyze",
            "evidence", "ledger", "directory"
        )
        if any(full_path == p or full_path.startswith(f"{p}/") for p in api_prefixes):
            raise HTTPException(status_code=404, detail="API route not found")

        target_file = dist_path / full_path
        if target_file.exists() and target_file.is_file():
            return FileResponse(target_file)

        # Fallback for cached clients requesting older asset bundles
        if full_path.startswith("assets/"):
            if full_path.endswith(".js"):
                js_files = list(assets_path.glob("*.js"))
                if js_files:
                    return FileResponse(js_files[0], media_type="application/javascript")
            elif full_path.endswith(".css"):
                css_files = list(assets_path.glob("*.css"))
                if css_files:
                    return FileResponse(css_files[0], media_type="text/css")

        if "." in Path(full_path).name or "download" in full_path:
            raise HTTPException(status_code=404, detail="Resource not found")

        return FileResponse(
            dist_path / "index.html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

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
