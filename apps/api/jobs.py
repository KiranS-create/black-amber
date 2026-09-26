import concurrent.futures
import threading
import uuid
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from apps.api.models import AnalysisJobResponse, JobStatus
from apps.api.storage import MetadataRepository, default_metadata_repo
from core.attribution.engine import AttributionResult, AttributionState

class JobManager:
    """
    Lightweight, in-process job manager for long-running forensic analysis tasks.
    Zero external broker dependencies (fully functional offline on single laptop).
    """
    def __init__(
        self,
        metadata_repo: Optional[MetadataRepository] = None,
        max_workers: int = 4
    ):
        self.metadata_repo = metadata_repo or default_metadata_repo
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="sih-analysis-worker"
        )
        self._lock = threading.Lock()

    def create_job(
        self,
        leak_id: Optional[str] = None,
        leak_artifact_hash: Optional[str] = None
    ) -> AnalysisJobResponse:
        analysis_id = f"job_anlz_{uuid.uuid4().hex[:10]}"
        job = AnalysisJobResponse(
            analysis_id=analysis_id,
            status=JobStatus.QUEUED,
            created_at=datetime.now(timezone.utc).isoformat(),
            leak_id=leak_id,
            leak_artifact_hash=leak_artifact_hash,
        )
        with self._lock:
            self.metadata_repo.save_job(job)
        return job

    def submit_job(
        self,
        job: AnalysisJobResponse,
        task_func: Callable[[], AttributionResult]
    ) -> AnalysisJobResponse:
        def _runner():
            with self._lock:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(timezone.utc).isoformat()
                self.metadata_repo.save_job(job)

            try:
                result = task_func()
                with self._lock:
                    job.completed_at = datetime.now(timezone.utc).isoformat()
                    job.result = result
                    if result.state == AttributionState.ATTRIBUTED:
                        job.status = JobStatus.COMPLETED
                    else:
                        job.status = JobStatus.ABSTAINED
                    self.metadata_repo.save_job(job)
            except Exception as e:
                with self._lock:
                    job.completed_at = datetime.now(timezone.utc).isoformat()
                    job.status = JobStatus.FAILED
                    job.error = f"{type(e).__name__}: {str(e)}"
                    self.metadata_repo.save_job(job)

        self.executor.submit(_runner)
        return job

    def execute_synchronously(
        self,
        job: AnalysisJobResponse,
        task_func: Callable[[], AttributionResult]
    ) -> AnalysisJobResponse:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc).isoformat()
        try:
            result = task_func()
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.result = result
            if result.state == AttributionState.ATTRIBUTED:
                job.status = JobStatus.COMPLETED
            else:
                job.status = JobStatus.ABSTAINED
        except Exception as e:
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.status = JobStatus.FAILED
            job.error = f"{type(e).__name__}: {str(e)}"

        with self._lock:
            self.metadata_repo.save_job(job)
        return job

    def get_job(self, analysis_id: str) -> Optional[AnalysisJobResponse]:
        with self._lock:
            return self.metadata_repo.get_job(analysis_id)

    def list_jobs(self) -> List[AnalysisJobResponse]:
        with self._lock:
            return self.metadata_repo.list_jobs()

default_job_manager = JobManager()
