from fastapi import APIRouter

from apps.api.config import config
from apps.api.models import CapabilitiesResponse, HealthResponse, LedgerVerifyResponse
from apps.api.orchestrator import default_orchestrator

router = APIRouter(tags=["System"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    """System health check and live operational metrics."""
    return HealthResponse(
        status="healthy",
        service="SIH26237 API",
        version=config.version,
        ledger_events_count=len(default_orchestrator.ledger.events),
        registered_documents_count=len(default_orchestrator.metadata_repo.list_documents()),
        enrolled_recipients_count=len(default_orchestrator.registry.list_all()),
        releases_count=len(default_orchestrator.release_manager.list_releases()),
        active_jobs_count=len(default_orchestrator.job_manager.list_jobs())
    )

@router.get("/capabilities", response_model=CapabilitiesResponse)
def get_capabilities():
    """
    Expose cryptographic, provenance, and forensic capabilities of the offline-first backend.
    """
    return CapabilitiesResponse(
        service_name="SIH26237 Cryptographic Attribution Platform",
        version=config.version,
        offline_mode=True,
        authentication_mode="BEARER_TOKEN_ACTOR" if config.enforce_auth else "PROTOTYPE_TOKEN_OR_ROLE",
        key_custody_model="DECENTRALIZED_CLIENT_CUSTODY",
        simulation_mode=config.server_key_custody,
        cryptography={
            "kem": "ML-KEM-768 (NIST FIPS 203)",
            "signature": "ML-DSA-65 (NIST FIPS 204)",
            "symmetric": "AES-256-GCM (NIST SP 800-38D)",
            "key_wrap": "AES Key Wrap (RFC 3394 / NIST SP 800-38F)",
            "derivation": "HKDF-SHA256 (RFC 5869) with domain separation",
            "hashing": "SHA-256 (FIPS 180-4)"
        },
        traceability={
            "algorithms": [
                "PrototypeTraceabilityProvider_v0.1 (HMAC-SHA256)",
                "TardosTraceabilityProvider_v1.0 (Symbol-Symmetric Tardos)"
            ],
            "capacity_planner": "TardosCapacityPlanner (Blayer-Tassa / Skoric bounds)",
            "marking_assumption_enforced": True
        },
        evidence_fusion={
            "engine": "Bayesian Multi-Channel Evidence Fusion",
            "channels": [
                "TARDOS_FINGERPRINT",
                "WATERMARK_PAYLOAD",
                "PROVENANCE_SIGNATURE",
                "AUDIT_LEDGER",
                "CRYPTOGRAPHIC_INTEGRITY",
                "ATTACK_CONTEXT"
            ],
            "anti_double_counting": "EvidenceDependencyGraph with Max Evidentiary Bound",
            "decision_policy": "Fail-Closed (Never Force an Attribution)"
        },
        watermarking={
            "adapter": "WatermarkAnalysisAdapter",
            "carrier_types": ["PHYSICAL_PRINT", "DIGITAL_IMAGE", "DIGITAL_PDF"],
            "physical_validation_available": True,
            "blind_extraction_supported": True
        },
        client_workflows={
            "recipient_decryption": "CLIENT_SIDE_LOCAL",
            "provenance_signing": "CLIENT_SIDE_ML_DSA_65",
            "server_provenance_endpoints": [
                "POST /evidence/decryption-events",
                "POST /releases/{release_id}/provenance"
            ],
            "simulated_local_oracle": "POST /releases/{release_id}/decrypt"
        },
        supported_formats=config.allowed_mime_types
    )

@router.get("/ledger/verify", response_model=LedgerVerifyResponse)
def verify_ledger():
    """Verify cryptographic hash-chain integrity of the tamper-evident ledger."""
    is_valid, count, tip, errors = default_orchestrator.verify_ledger()
    return LedgerVerifyResponse(
        is_valid=is_valid,
        total_events=count,
        chain_tip=tip,
        errors=errors
    )
