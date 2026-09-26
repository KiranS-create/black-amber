import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    title: str = "SIH26237 — Cryptographic Attribution & Provenance API"
    version: str = "1.0.0"
    description: str = (
        "Production-grade, offline-first orchestration layer for post-quantum "
        "multi-recipient document distribution, decentralized decryption provenance, "
        "and fail-closed leak attribution."
    )
    
    # Storage settings
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    data_dir: Path = base_dir / "data"
    artifacts_dir: Path = data_dir / "artifacts"
    db_path: Path = data_dir / "metadata.sqlite3"
    
    # Upload & Payload limits
    max_upload_size_bytes: int = 50 * 1024 * 1024  # 50 MB ceiling
    allowed_mime_types: list[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "application/octet-stream",
    ]
    
    # Cryptographic & Traceability Defaults
    default_issuer_id: str = "HQ_AUTHORITY"
    default_coalition_size: int = 3
    default_false_accusation_epsilon: float = 1e-4
    default_kappa_factor: float = 20.0
    default_tardos_recipient_hint: int = 10
    
    # CORS Configuration
    allowed_cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Security & Role-Based Access Control
    enforce_auth: bool = False  # Set to True for strict authorization enforcement
    require_role_header: bool = False  # Set to True to strictly enforce role headers on all endpoints
    valid_roles: list[str] = ["authority", "recipient", "auditor", "system"]
    
    # Local Prototype Auth Token Store (Maps Bearer tokens to (role, actor_id))
    local_auth_tokens: Dict[str, Dict[str, str]] = Field(default_factory=lambda: {
        "token_authority_hq": {"role": "authority", "actor_id": "HQ_AUTHORITY"},
        "token_auditor_sec": {"role": "auditor", "actor_id": "AUDITOR_PRIMARY"},
        "token_system_internal": {"role": "system", "actor_id": "SYSTEM_DAEMON"},
        "token_alice": {"role": "recipient", "actor_id": "alice"},
        "token_bob": {"role": "recipient", "actor_id": "bob"},
        "token_charlie": {"role": "recipient", "actor_id": "charlie"},
    })

    # Client-side vs Server-side Key Custody mode
    server_key_custody: bool = False  # False = Decentralized (client holds private keys)

config = AppConfig()

# Ensure directories exist
config.artifacts_dir.mkdir(parents=True, exist_ok=True)
