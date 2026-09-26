import base64
import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.recipient import RecipientRegistry, Recipient, PublicRecipient, default_registry
from core.release import ReleaseManager, DocumentRelease, ReleaseRecipientPackage, default_release_manager
from core.provenance.decryption import RecipientDecryptionClient, default_decryption_client
from core.traceability.provider import PrototypeTraceabilityProvider, TardosTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent, default_ledger
from core.attribution.engine import AttributionEngine, AttributionResult, default_attribution_engine

from apps.api.config import config
from apps.api.errors import (
    APIException,
    ArtifactHashMismatchError,
    ArtifactNotFoundError,
    CapacityInsufficientError,
    DocumentNotFoundError,
    ErrorCode,
    RecipientNotFoundError,
    ReleaseNotFoundError,
)
from apps.api.models import (
    AnalysisJobResponse,
    ArtifactMetadata,
    ArtifactType,
    CreateReleaseRequest,
    DecryptionResponse,
    DocumentMetadata,
    JobStatus,
    LeakMetadata,
)
from apps.api.storage import (
    ArtifactStorage,
    MetadataRepository,
    default_artifact_storage,
    default_metadata_repo,
)
from apps.api.jobs import JobManager, default_job_manager
from apps.api.adapters import (
    WatermarkAnalysisAdapter,
    AttackContextAdapter,
    TraceabilityAdapter,
    EvidenceFusionAdapter,
)

class SystemOrchestrator:
    """
    Central orchestration service for the SIH26237 backend.
    Orchestrates the existing cryptography, release machinery, traceability providers,
    tamper-evident ledger, and attribution fusion engine without duplicating internal logic.
    """
    def __init__(
        self,
        registry: Optional[RecipientRegistry] = None,
        release_manager: Optional[ReleaseManager] = None,
        decryption_client: Optional[RecipientDecryptionClient] = None,
        ledger: Optional[TamperEvidentLedger] = None,
        attribution_engine: Optional[AttributionEngine] = None,
        artifact_storage: Optional[ArtifactStorage] = None,
        metadata_repo: Optional[MetadataRepository] = None,
        job_manager: Optional[JobManager] = None,
    ):
        self.registry = registry or default_registry
        self.release_manager = release_manager or default_release_manager
        self.decryption_client = decryption_client or default_decryption_client
        self.ledger = ledger or default_ledger
        self.attribution_engine = attribution_engine or default_attribution_engine
        self.storage = artifact_storage or default_artifact_storage
        self.metadata_repo = metadata_repo or default_metadata_repo
        self.job_manager = job_manager or default_job_manager

        # Forensic adapters
        self.watermark_adapter = WatermarkAnalysisAdapter()
        self.attack_adapter = AttackContextAdapter()
        self.traceability_adapter = TraceabilityAdapter()
        self.fusion_adapter = EvidenceFusionAdapter(self.attribution_engine)

    # 1. Document Lifecycle
    def register_document(
        self,
        document_bytes: bytes,
        document_name: str,
        document_id: Optional[str] = None,
        mime_type: str = "application/pdf"
    ) -> DocumentMetadata:
        orig_hash = hashlib.sha256(document_bytes).hexdigest()
        doc_id = document_id or f"doc_{orig_hash[:8]}_{uuid.uuid4().hex[:6]}"

        # Store in Data Plane
        artifact = self.storage.store_artifact(
            data=document_bytes,
            artifact_type=ArtifactType.ORIGINAL_DOCUMENT,
            document_id=doc_id,
            mime_type=mime_type,
            expected_hash=orig_hash
        )

        doc_meta = DocumentMetadata(
            document_id=doc_id,
            document_name=document_name,
            original_document_hash=orig_hash,
            size_bytes=len(document_bytes),
            mime_type=mime_type,
            created_at=artifact.created_at,
            artifact_id=artifact.artifact_id
        )

        # Store in Control Plane
        self.metadata_repo.save_document(doc_meta)
        return doc_meta

    def get_document(self, document_id: str) -> DocumentMetadata:
        doc = self.metadata_repo.get_document(document_id)
        if not doc:
            raise DocumentNotFoundError(document_id)
        return doc

    def get_document_bytes(self, document_id: str) -> bytes:
        doc = self.get_document(document_id)
        return self.storage.retrieve_artifact_bytes(doc.artifact_id)

    # 2. Recipient Lifecycle
    def enroll_recipient(self, name: str, recipient_id: Optional[str] = None) -> PublicRecipient:
        rec = self.registry.enroll(name=name, recipient_id=recipient_id)
        return rec.to_public()

    def list_recipients(self) -> List[PublicRecipient]:
        return self.registry.list_public()

    def get_recipient(self, recipient_id: str) -> PublicRecipient:
        rec = self.registry.get(recipient_id)
        if not rec:
            raise RecipientNotFoundError(recipient_id)
        return rec.to_public()

    # 3. Release Lifecycle
    def create_release(self, req: CreateReleaseRequest) -> DocumentRelease:
        # Resolve document bytes
        if req.document_id:
            doc = self.get_document(req.document_id)
            doc_bytes = self.storage.retrieve_artifact_bytes(doc.artifact_id)
            doc_name = req.document_name or doc.document_name
            doc_id = doc.document_id
        elif req.document_base64:
            try:
                from security.defense import validate_base64_payload
                doc_bytes = validate_base64_payload(
                    req.document_base64,
                    max_size_bytes=config.max_upload_size_bytes
                )
            except Exception as e:
                raise APIException(
                    code=ErrorCode.INVALID_RELEASE,
                    message=f"Invalid or oversized base64 payload for document: {str(e)}"
                )
            doc_name = req.document_name or "Untitled.pdf"
            # Auto-register document
            doc_meta = self.register_document(doc_bytes, doc_name)
            doc_id = doc_meta.document_id
        else:
            raise APIException(
                code=ErrorCode.INVALID_RELEASE,
                message="Either 'document_id' or 'document_base64' must be provided."
            )

        # Validate recipient population
        for r_id in req.recipient_ids:
            if not self.registry.get(r_id):
                raise RecipientNotFoundError(r_id)

        # Tardos capacity check if requested
        if req.tardos_enabled:
            feasible, reason, req_len = self.traceability_adapter.validate_capacity(
                recipient_count=len(req.recipient_ids),
                coalition_size=req.coalition_size,
                false_accusation_epsilon=req.false_accusation_epsilon,
                carrier_budget=req.carrier_budget
            )
            if not feasible:
                raise CapacityInsufficientError(
                    reason=reason or "Carrier budget too small for requested parameters.",
                    details={"required_symbols": req_len, "available_symbols": req.carrier_budget}
                )

        # Invoke release manager to perform ML-KEM + AES-256-GCM packaging
        release = self.release_manager.create_release(
            document_bytes=doc_bytes,
            document_name=doc_name,
            issuer_id=req.issuer_id,
            recipient_ids=req.recipient_ids,
            document_id=doc_id
        )

        return release

    def get_release(self, release_id: str) -> DocumentRelease:
        release = self.release_manager.get_release(release_id)
        if not release:
            raise ReleaseNotFoundError(release_id)
        return release

    def list_releases(self) -> List[DocumentRelease]:
        return self.release_manager.list_releases()

    def get_recipient_package(self, release_id: str, recipient_id: str) -> ReleaseRecipientPackage:
        pkg = self.release_manager.get_recipient_package(release_id, recipient_id)
        if not pkg:
            raise APIException(
                code=ErrorCode.RELEASE_NOT_FOUND,
                message=f"No package found for recipient '{recipient_id}' in release '{release_id}'."
            )
        return pkg

    # 4. Decryption & Provenance Signing
    def decrypt_release_package(self, release_id: str, recipient_id: str) -> DecryptionResponse:
        release = self.get_release(release_id)
        package = self.get_recipient_package(release_id, recipient_id)
        recipient = self.registry.get(recipient_id)
        if not recipient:
            raise RecipientNotFoundError(recipient_id)

        try:
            plaintext, traceable_copy, event, event_hash = self.decryption_client.decrypt_package(
                package=package,
                recipient=recipient
            )
        except Exception as e:
            raise APIException(
                code=ErrorCode.INVALID_RELEASE,
                message=f"Decryption failed: {str(e)}"
            )

        orig_hash = hashlib.sha256(plaintext).hexdigest()
        traceable_hash = hashlib.sha256(traceable_copy).hexdigest()

        # Store traceable copy in Data Plane
        artifact = self.storage.store_artifact(
            data=traceable_copy,
            artifact_type=ArtifactType.DECRYPTED_TRACEABLE,
            document_id=package.document_id,
            release_id=release_id,
            recipient_id=recipient_id,
            expected_hash=traceable_hash
        )

        return DecryptionResponse(
            status="SUCCESS",
            release_id=release_id,
            document_id=package.document_id,
            recipient_id=recipient_id,
            original_document_hash=orig_hash,
            traceable_artifact_hash=traceable_hash,
            event_id=event.event_id,
            event_hash=event_hash,
            timestamp=event.timestamp,
            simulation_mode=True,
            provenance_mode="SIMULATED_LOCAL_ORACLE",
            traceable_document_base64=base64.b64encode(traceable_copy).decode('utf-8')
        )

    # 5. Leak Ingestion
    def ingest_leak(
        self,
        leak_bytes: bytes,
        mime_type: str = "application/pdf",
        suspected_document_id: Optional[str] = None,
        suspected_release_id: Optional[str] = None
    ) -> LeakMetadata:
        leak_hash = hashlib.sha256(leak_bytes).hexdigest()
        leak_id = f"leak_{leak_hash[:8]}_{uuid.uuid4().hex[:6]}"

        artifact = self.storage.store_artifact(
            data=leak_bytes,
            artifact_type=ArtifactType.LEAK_ARTIFACT,
            document_id=suspected_document_id,
            release_id=suspected_release_id,
            mime_type=mime_type,
            expected_hash=leak_hash
        )

        meta = LeakMetadata(
            leak_id=leak_id,
            leak_artifact_hash=leak_hash,
            size_bytes=len(leak_bytes),
            mime_type=mime_type,
            suspected_document_id=suspected_document_id,
            suspected_release_id=suspected_release_id,
            created_at=artifact.created_at,
            artifact_id=artifact.artifact_id
        )
        self.metadata_repo.save_leak(meta)
        return meta

    def get_leak(self, leak_id: str) -> LeakMetadata:
        leak = self.metadata_repo.get_leak(leak_id)
        if not leak:
            raise APIException(
                code=ErrorCode.ARTIFACT_NOT_FOUND,
                message=f"Leak artifact with ID '{leak_id}' not found."
            )
        return leak

    # 6. Leak Analysis Orchestration
    def analyze_leak(
        self,
        leak_id: Optional[str] = None,
        leaked_document_base64: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        expected_document_id: Optional[str] = None,
        attack_telemetry: Optional[Any] = None,
        async_execution: bool = False
    ) -> AnalysisJobResponse:
        # Resolve leak bytes
        if leak_id:
            leak_meta = self.get_leak(leak_id)
            leak_bytes = self.storage.retrieve_artifact_bytes(leak_meta.artifact_id)
            leak_hash = leak_meta.leak_artifact_hash
            exp_rel = expected_release_id or leak_meta.suspected_release_id
            exp_doc = expected_document_id or leak_meta.suspected_document_id
        elif leaked_document_base64:
            try:
                from security.defense import validate_base64_payload
                leak_bytes = validate_base64_payload(
                    leaked_document_base64,
                    max_size_bytes=config.max_upload_size_bytes
                )
            except Exception as e:
                raise APIException(
                    code=ErrorCode.INVALID_ANALYSIS_REQUEST,
                    message=f"Invalid or oversized base64 payload for leaked document: {str(e)}"
                )
            # Auto-ingest into storage
            leak_meta = self.ingest_leak(
                leak_bytes,
                suspected_document_id=expected_document_id,
                suspected_release_id=expected_release_id
            )
            leak_id = leak_meta.leak_id
            leak_hash = leak_meta.leak_artifact_hash
            exp_rel = expected_release_id
            exp_doc = expected_document_id
        else:
            raise APIException(
                code=ErrorCode.INVALID_ANALYSIS_REQUEST,
                message="Either 'leak_id' or 'leaked_document_base64' must be provided."
            )

        job = self.job_manager.create_job(leak_id=leak_id, leak_artifact_hash=leak_hash)

        def _task():
            return self.fusion_adapter.execute_fusion(
                leaked_bytes=leak_bytes,
                expected_release_id=exp_rel,
                expected_document_id=exp_doc,
                attack_telemetry=attack_telemetry
            )

        if async_execution:
            return self.job_manager.submit_job(job, _task)
        else:
            return self.job_manager.execute_synchronously(job, _task)

    def get_analysis_job(self, analysis_id: str) -> AnalysisJobResponse:
        job = self.job_manager.get_job(analysis_id)
        if not job:
            raise APIException(
                code=ErrorCode.ARTIFACT_NOT_FOUND,
                message=f"Analysis job with ID '{analysis_id}' not found."
            )
        return job

    def list_analysis_jobs(self) -> List[AnalysisJobResponse]:
        return self.job_manager.list_jobs()

    # 7. Audit & Verification
    def get_release_evidence(self, release_id: str) -> List[EvidenceEvent]:
        return self.ledger.get_events_for_release(release_id)

    def submit_decryption_event(self, event: EvidenceEvent) -> str:
        """
        Verify cryptographic provenance and append a client-signed EvidenceEvent to the ledger.
        Verifies:
        1. Recipient is registered and holds a valid enrolled ML-DSA-65 public key.
        2. Release exists and recipient is an authorized recipient.
        3. Document ID matches the release's master document.
        4. ML-DSA-65 digital signature is cryptographically valid over the bound provenance payload.
        5. Event does not violate anti-replay constraints or hash chain continuity in the ledger.
        """
        recipient = self.registry.get(event.recipient_id)
        if not recipient:
            raise RecipientNotFoundError(event.recipient_id)

        # 1. Release & Document Binding Checks
        release = self.get_release(event.release_id)
        if event.document_id != release.document_id:
            raise APIException(
                code=ErrorCode.INVALID_RELEASE,
                message=f"Document ID mismatch: release '{event.release_id}' binds document '{release.document_id}', but event specifies '{event.document_id}'.",
                status_code=400
            )

        if event.recipient_id not in release.recipient_ids:
            raise APIException(
                code=ErrorCode.INVALID_RELEASE,
                message=f"Unauthorized recipient: recipient '{event.recipient_id}' is not an authorized recipient for release '{event.release_id}'.",
                status_code=400
            )

        # 2. Reconstruct exact sign payload
        sign_payload = (
            f"DECRYPTION_PROVENANCE:{event.event_id}:{event.document_id}:"
            f"{event.release_id}:{event.recipient_id}:{event.artifact_hash}:"
            f"{event.previous_event_hash}:{event.timestamp}"
        ).encode('utf-8')

        pub_key_bytes = None
        if recipient.dsa_keypair and recipient.dsa_keypair.public_key_bytes:
            pub_key_bytes = recipient.dsa_keypair.public_key_bytes
        elif recipient.dsa_public_key_b64:
            pub_key_bytes = base64.b64decode(recipient.dsa_public_key_b64)

        if not pub_key_bytes:
            raise APIException(
                code=ErrorCode.INVALID_SIGNATURE,
                message=f"No enrolled ML-DSA-65 public key found for recipient '{event.recipient_id}'.",
                status_code=400
            )

        try:
            sig_bytes = base64.b64decode(event.signature)
        except Exception:
            raise APIException(
                code=ErrorCode.INVALID_SIGNATURE,
                message="Malformed base64 signature on evidence event.",
                status_code=400
            )

        from core.crypto.signatures import MLDSA65
        if not MLDSA65.verify(pub_key_bytes, sign_payload, sig_bytes):
            raise APIException(
                code=ErrorCode.INVALID_SIGNATURE,
                message="Cryptographic verification failed: invalid ML-DSA-65 signature for decryption event.",
                status_code=400
            )

        # 3. Append to Ledger with Replay & Chain Tip Verification
        try:
            event_hash = self.ledger.append_event(event)
        except ValueError as ve:
            raise APIException(
                code=ErrorCode.INVALID_RELEASE,
                message=f"Ledger event rejection: {str(ve)}",
                status_code=400
            )
        return event_hash

    def verify_ledger(self) -> Tuple[bool, int, str, List[str]]:
        is_valid, errors = self.ledger.verify_chain()
        return is_valid, len(self.ledger.events), self.ledger.get_last_event_hash(), errors

default_orchestrator = SystemOrchestrator()
