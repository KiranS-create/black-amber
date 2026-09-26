from typing import List, Optional
from fastapi import APIRouter, Depends, status

from apps.api.models import (
    AnalysisJobResponse,
    AnalysisListResponse,
    AnalyzeRequest,
    JobStatus,
)
from apps.api.orchestrator import default_orchestrator
from apps.api.security import Actor, require_role
from core.attribution.engine import AttributionResult

router = APIRouter(tags=["Analysis"])

@router.post("/analyze", response_model=AnalysisJobResponse, status_code=status.HTTP_200_OK)
def analyze_leak(
    req: AnalyzeRequest,
    actor: Actor = Depends(require_role(["authority", "auditor", "system"]))
):
    """
    Execute forensic leak analysis:
    - Extracts traceability marker / Tardos fingerprint symbols.
    - Runs physical/digital watermark adapter.
    - Correlates recipient decryption provenance events from ledger.
    - Verifies ML-DSA-65 post-quantum signatures.
    - Performs multi-channel Bayesian evidence fusion under fail-closed policy.
    - Supports both synchronous immediate response and asynchronous polling.
    """
    job = default_orchestrator.analyze_leak(
        leak_id=req.leak_id,
        leaked_document_base64=req.leaked_document_base64,
        expected_release_id=req.expected_release_id,
        expected_document_id=req.expected_document_id,
        attack_telemetry=req.attack_telemetry,
        async_execution=req.async_execution
    )
    return job

@router.get("/analysis", response_model=AnalysisListResponse)
def list_analysis_jobs(
    actor: Actor = Depends(require_role(["authority", "auditor", "system"]))
):
    """List all submitted forensic analysis jobs and their statuses."""
    jobs = default_orchestrator.list_analysis_jobs()
    return AnalysisListResponse(jobs=jobs, total=len(jobs))

@router.get("/analysis/{analysis_id}", response_model=AnalysisJobResponse)
def get_analysis_job(
    analysis_id: str,
    actor: Actor = Depends(require_role(["authority", "auditor", "system"]))
):
    """Retrieve detailed execution status and forensic attribution findings for an analysis job."""
    return default_orchestrator.get_analysis_job(analysis_id)
