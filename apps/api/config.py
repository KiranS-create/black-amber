import os
from pathlib import Path
from typing import Any, Dict, List, Optional
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
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "text/csv",
        "application/rtf",
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
    valid_roles: List[str] = [
        "administrator",
        "investigator",
        "operator",
        "viewer",
        "recipient",
        "device",
        "service_account",
        # Backward-compatibility legacy roles:
        "authority",
        "auditor",
        "system"
    ]
    
    # Rate Limiting Configuration
    rate_limit_enabled: bool = True
    rate_limit_default: int = 100       # General API requests per minute
    rate_limit_crypto: int = 20         # Crypto/Attribution intensive requests per minute
    rate_limit_upload: int = 10         # Artifact uploads per minute
    rate_limit_window_seconds: int = 60

    # Anti-Replay Protection Configuration
    replay_window_seconds: int = 300   # 5-minute replay tolerance window

    # Multi-Tenant Local Auth Token Store
    # Maps Bearer tokens to validated server-side principal context
    local_auth_tokens: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        # Tenant A Principals
        "token_admin_tenant_a": {"role": "administrator", "actor_id": "admin_a", "tenant_id": "tenant_a", "scopes": ["*"]},
        "token_investigator_tenant_a": {"role": "investigator", "actor_id": "inv_a", "tenant_id": "tenant_a", "scopes": ["read", "analyze"]},
        "token_operator_tenant_a": {"role": "operator", "actor_id": "op_a", "tenant_id": "tenant_a", "scopes": ["create_release", "upload_doc"]},
        "token_viewer_tenant_a": {"role": "viewer", "actor_id": "view_a", "tenant_id": "tenant_a", "scopes": ["read"]},
        "token_alice_tenant_a": {"role": "recipient", "actor_id": "alice", "tenant_id": "tenant_a", "scopes": ["decrypt", "provenance"]},
        "token_bob_tenant_a": {"role": "recipient", "actor_id": "bob", "tenant_id": "tenant_a", "scopes": ["decrypt", "provenance"]},
        "token_device_tenant_a": {"role": "device", "actor_id": "kiosk_01", "tenant_id": "tenant_a", "scopes": ["telemetry"]},
        "token_service_tenant_a": {"role": "service_account", "actor_id": "svc_ingest", "tenant_id": "tenant_a", "scopes": ["ingest"]},

        # Tenant B Principals
        "token_admin_tenant_b": {"role": "administrator", "actor_id": "admin_b", "tenant_id": "tenant_b", "scopes": ["*"]},
        "token_investigator_tenant_b": {"role": "investigator", "actor_id": "inv_b", "tenant_id": "tenant_b", "scopes": ["read", "analyze"]},
        "token_charlie_tenant_b": {"role": "recipient", "actor_id": "charlie", "tenant_id": "tenant_b", "scopes": ["decrypt", "provenance"]},

        # Demo Tenant Principals (Isolated for SIH Judge Demonstrations)
        "token_demo_admin": {"role": "administrator", "actor_id": "demo_admin", "tenant_id": "demo_tenant", "scopes": ["demo:*", "read", "write"]},

        # Legacy backward-compatible prototype tokens (mapped to default_tenant)
        "token_authority_hq": {"role": "authority", "actor_id": "HQ_AUTHORITY", "tenant_id": "default_tenant", "scopes": ["*"]},
        "token_auditor_sec": {"role": "auditor", "actor_id": "AUDITOR_PRIMARY", "tenant_id": "default_tenant", "scopes": ["read", "analyze"]},
        "token_system_internal": {"role": "system", "actor_id": "SYSTEM_DAEMON", "tenant_id": "default_tenant", "scopes": ["*"]},
        "token_alice": {"role": "recipient", "actor_id": "alice", "tenant_id": "default_tenant", "scopes": ["decrypt", "provenance"]},
        "token_bob": {"role": "recipient", "actor_id": "bob", "tenant_id": "default_tenant", "scopes": ["decrypt", "provenance"]},
        "token_charlie": {"role": "recipient", "actor_id": "charlie", "tenant_id": "default_tenant", "scopes": ["decrypt", "provenance"]},
    })

    # Demo Authentication Settings
    demo_auth_enabled: bool = Field(
        default_factory=lambda: os.getenv("DEMO_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")
    )
    demo_username: str = Field(
        default_factory=lambda: os.getenv("DEMO_USERNAME", "admin")
    )
    demo_password: str = Field(
        default_factory=lambda: os.getenv("DEMO_PASSWORD", "admin")
    )
    demo_tenant_id: str = "demo_tenant"

    # Base URLs for Hosted & Free Deployments
    public_base_url: str = Field(
        default_factory=lambda: os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
    )
    api_base_url: str = Field(
        default_factory=lambda: os.getenv("API_BASE_URL", "http://localhost:8000")
    )

    # Client-side vs Server-side Key Custody mode
    server_key_custody: bool = False  # False = Decentralized (client holds private keys)

config = AppConfig()

# Ensure directories exist
config.artifacts_dir.mkdir(parents=True, exist_ok=True)
