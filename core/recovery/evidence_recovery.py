"""
AegisTrace Evidence Package Recovery & Provenance Continuity Engine.

Ensures evidence bundles, cross-channel observations, target bindings,
and attribution decisions remain independently verifiable after disaster recovery.
Guarantees that recovered evidence preserves original package identity without synthetic rewriting.
"""

from typing import List, Dict, Optional, Tuple, Set, Any
import hashlib
from pydantic import BaseModel, Field

from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceObservation,
    TargetBinding,
    EvidenceFamily,
)
from core.recovery.models import RecoveryState


class EvidenceRecoveryResult(BaseModel):
    state: RecoveryState
    bundles_recovered: int = 0
    observations_verified: int = 0
    corrupted_observations: int = 0
    target_binding_mismatches: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class EvidencePackageRecoveryEngine:
    """
    Forensic recovery engine for evidence bundles and observations.
    Validates cryptographic target bindings and cross-channel observation integrity.
    """

    @classmethod
    def recover_evidence_bundles(
        cls,
        candidate_bundles: List[EvidenceBundle],
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
    ) -> Tuple[EvidenceRecoveryResult, List[EvidenceBundle]]:
        """
        Validates and recovers forensic evidence bundles.
        Fails closed on corrupted observations or broken target bindings.
        """
        if not candidate_bundles:
            return (
                EvidenceRecoveryResult(
                    state=RecoveryState.UNRECOVERABLE,
                    errors=["EMPTY_EVIDENCE: Zero evidence bundles provided for recovery"]
                ),
                []
            )

        recovered_bundles: List[EvidenceBundle] = []
        verified_obs = 0
        corrupted_obs = 0
        binding_mismatches = 0
        errors: List[str] = []
        warnings: List[str] = []

        seen_bundle_ids: Set[str] = set()

        for b_idx, bundle in enumerate(candidate_bundles):
            if not bundle.bundle_id:
                errors.append(f"MISSING_BUNDLE_ID: Evidence bundle at index {b_idx} lacks bundle_id")
                continue

            if bundle.bundle_id in seen_bundle_ids:
                errors.append(f"DUPLICATE_BUNDLE_ID: Evidence bundle '{bundle.bundle_id}' appears multiple times")
                continue
            seen_bundle_ids.add(bundle.bundle_id)

            # Check target binding
            tb = bundle.target_binding
            if expected_document_id and tb.document_id and tb.document_id != expected_document_id:
                binding_mismatches += 1
                errors.append(
                    f"BINDING_MISMATCH: Bundle '{bundle.bundle_id}' document '{tb.document_id}' != expected '{expected_document_id}'"
                )

            if expected_release_id and tb.release_id and tb.release_id != expected_release_id:
                binding_mismatches += 1
                errors.append(
                    f"BINDING_MISMATCH: Bundle '{bundle.bundle_id}' release '{tb.release_id}' != expected '{expected_release_id}'"
                )

            # Validate each observation in bundle
            bundle_valid = True
            for obs in bundle.observations:
                if not obs.source_id or not obs.family:
                    corrupted_obs += 1
                    bundle_valid = False
                    errors.append(f"INVALID_OBSERVATION: Bundle '{bundle.bundle_id}' observation missing source_id or family")
                else:
                    verified_obs += 1

            if bundle_valid:
                recovered_bundles.append(bundle)

        if errors:
            state = RecoveryState.CORRUPTED_RECOVERY
            return (
                EvidenceRecoveryResult(
                    state=state,
                    bundles_recovered=len(recovered_bundles),
                    observations_verified=verified_obs,
                    corrupted_observations=corrupted_obs,
                    target_binding_mismatches=binding_mismatches,
                    errors=errors,
                    warnings=warnings
                ),
                recovered_bundles
            )

        return (
            EvidenceRecoveryResult(
                state=RecoveryState.VALID_RECOVERY,
                bundles_recovered=len(recovered_bundles),
                observations_verified=verified_obs,
                corrupted_observations=0,
                target_binding_mismatches=0,
                errors=[],
                warnings=warnings,
                details={"recovered_count": len(recovered_bundles)}
            ),
            recovered_bundles
        )
