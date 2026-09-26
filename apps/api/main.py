import os
import io
import base64
import hashlib
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.recipient import RecipientRegistry, PublicRecipient, default_registry
from core.release import ReleaseManager, DocumentRelease, ReleaseRecipientPackage, default_release_manager
from core.provenance.decryption import RecipientDecryptionClient, default_decryption_client
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent, default_ledger
from core.attribution.engine import AttributionEngine, AttributionResult, default_attribution_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    default_registry.init_demo_recipients()
    yield
    # Shutdown

app = FastAPI(
    title="SIH26237 — Cryptographic Attribution & Provenance API",
    version="0.1.0",
    description="Post-quantum multi-recipient document distribution and tamper-evident decryption provenance API.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class EnrollRecipientRequest(BaseModel):
    name: str
    recipient_id: Optional[str] = None

class CreateReleaseRequest(BaseModel):
    document_name: str
    document_base64: str
    issuer_id: str = "HQ_AUTHORITY"
    recipient_ids: List[str]

class DecryptRequest(BaseModel):
    recipient_id: str

class AnalyzeLeakRequest(BaseModel):
    leaked_document_base64: str
    release_id: Optional[str] = None

# Routes
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "SIH26237 API",
        "version": "0.1.0",
        "ledger_events_count": len(default_ledger.events)
    }

@app.post("/recipients", response_model=PublicRecipient, tags=["Recipients"])
def enroll_recipient(req: EnrollRecipientRequest):
    recipient = default_registry.enroll(name=req.name, recipient_id=req.recipient_id)
    return recipient.to_public()

@app.get("/recipients", response_model=List[PublicRecipient], tags=["Recipients"])
def list_recipients():
    return default_registry.list_public()

@app.post("/releases", response_model=DocumentRelease, tags=["Releases"])
def create_release(req: CreateReleaseRequest):
    try:
        doc_bytes = base64.b64decode(req.document_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid document base64 payload")

    try:
        release = default_release_manager.create_release(
            document_bytes=doc_bytes,
            document_name=req.document_name,
            issuer_id=req.issuer_id,
            recipient_ids=req.recipient_ids
        )
        return release
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/releases", response_model=List[DocumentRelease], tags=["Releases"])
def list_releases():
    return default_release_manager.list_releases()

@app.get("/releases/{release_id}", response_model=DocumentRelease, tags=["Releases"])
def get_release(release_id: str):
    rel = default_release_manager.get_release(release_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Release not found")
    return rel

@app.post("/releases/{release_id}/decrypt", tags=["Decryption"])
def decrypt_release_package(release_id: str, req: DecryptRequest):
    release = default_release_manager.get_release(release_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    
    package = default_release_manager.get_recipient_package(release_id, req.recipient_id)
    if not package:
        raise HTTPException(status_code=404, detail=f"No package found for recipient {req.recipient_id}")

    recipient = default_registry.get(req.recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not enrolled")

    try:
        plaintext, traceable_copy, event, event_hash = default_decryption_client.decrypt_package(
            package=package,
            recipient=recipient
        )
        return {
            "status": "SUCCESS",
            "release_id": release_id,
            "recipient_id": req.recipient_id,
            "document_hash": package.document_hash,
            "traceable_document_base64": base64.b64encode(traceable_copy).decode('utf-8'),
            "event_id": event.event_id,
            "event_hash": event_hash,
            "timestamp": event.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")

@app.post("/leaks/analyze", response_model=AttributionResult, tags=["Attribution"])
def analyze_leak(req: AnalyzeLeakRequest):
    try:
        leaked_bytes = base64.b64decode(req.leaked_document_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid leaked document base64 payload")

    result = default_attribution_engine.analyze_leak(
        leaked_document_bytes=leaked_bytes,
        expected_release_id=req.release_id
    )
    return result

@app.get("/evidence/{release_id}", response_model=List[EvidenceEvent], tags=["Audit"])
def get_release_evidence(release_id: str):
    return default_ledger.get_events_for_release(release_id)

@app.get("/ledger/verify", tags=["Audit"])
def verify_ledger():
    is_valid, errors = default_ledger.verify_chain()
    return {
        "is_valid": is_valid,
        "total_events": len(default_ledger.events),
        "chain_tip": default_ledger.get_last_event_hash(),
        "errors": errors
    }
