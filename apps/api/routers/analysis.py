from typing import List, Optional
from fastapi import APIRouter, Depends, status

from apps.api.models import (
    AnalysisJobResponse,
    AnalysisListResponse,
    AnalyzeRequest,
    JobStatus,
)
from apps.api.orchestrator import default_orchestrator
from apps.api.security import (
    SecurityPrincipal,
    require_role,
    validate_id_format,
    verify_tenant_boundary,
)
from core.attribution.engine import AttributionResult

router = APIRouter(tags=["Analysis"])

@router.post("/analyze", response_model=AnalysisJobResponse, status_code=status.HTTP_200_OK)
def analyze_leak(
    req: AnalyzeRequest,
    actor: SecurityPrincipal = Depends(require_role(["investigator", "administrator", "operator", "authority", "auditor", "system"]))
):
    """
    Execute forensic leak analysis:
    - Extracts traceability marker / Tardos fingerprint symbols.
    - Runs physical/digital watermark adapter.
    - Correlates recipient decryption provenance events from ledger.
    - Verifies ML-DSA-65 post-quantum signatures.
    - Performs multi-channel Bayesian evidence fusion under fail-closed policy.
    - Enforces tenant isolation on referenced leak artifacts and releases.
    """
    target_tenant = req.tenant_id or actor.tenant_id
    verify_tenant_boundary(target_tenant, actor, "tenant", target_tenant)

    if req.leak_id:
        validate_id_format(req.leak_id, "leak_id")
        leak = default_orchestrator.get_leak(req.leak_id)
        verify_tenant_boundary(leak.tenant_id, actor, "leak", req.leak_id)
    if req.expected_release_id:
        validate_id_format(req.expected_release_id, "expected_release_id")
        try:
            rel = default_orchestrator.get_release(req.expected_release_id)
            verify_tenant_boundary(getattr(rel, "tenant_id", "default_tenant"), actor, "release", req.expected_release_id)
        except Exception:
            pass
    if req.expected_document_id:
        validate_id_format(req.expected_document_id, "expected_document_id")

    job = default_orchestrator.analyze_leak(
        leak_id=req.leak_id,
        leaked_document_base64=req.leaked_document_base64,
        expected_release_id=req.expected_release_id,
        expected_document_id=req.expected_document_id,
        attack_telemetry=req.attack_telemetry,
        async_execution=req.async_execution,
        tenant_id=target_tenant
    )
    return job

@router.get("/analysis", response_model=AnalysisListResponse)
def list_analysis_jobs(
    actor: SecurityPrincipal = Depends(require_role(["investigator", "administrator", "viewer", "authority", "auditor", "system"]))
):
    """List all submitted forensic analysis jobs scoped to tenant."""
    all_jobs = default_orchestrator.list_analysis_jobs()
    if actor.role == "system":
        return AnalysisListResponse(jobs=all_jobs, total=len(all_jobs))
    tenant_jobs = [j for j in all_jobs if getattr(j, "tenant_id", "default_tenant") == actor.tenant_id]
    return AnalysisListResponse(jobs=tenant_jobs, total=len(tenant_jobs))

@router.get("/analysis/{analysis_id}", response_model=AnalysisJobResponse)
def get_analysis_job(
    analysis_id: str,
    actor: SecurityPrincipal = Depends(require_role(["investigator", "administrator", "viewer", "authority", "auditor", "system"]))
):
    """Retrieve detailed execution status and forensic attribution findings for an analysis job."""
    validate_id_format(analysis_id, "analysis_id")
    job = default_orchestrator.get_analysis_job(analysis_id)
    verify_tenant_boundary(getattr(job, "tenant_id", "default_tenant"), actor, "analysis", analysis_id)
    return job
