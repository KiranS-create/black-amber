"""
SIH26237 - Forensic Evaluation Corpora & Population Builder
Constructs standardized, deterministically seeded, and content-hashed evaluation populations
strictly partitioned into non-overlapping CALIBRATION, VALIDATION, and HELD_OUT_TEST splits.
"""

import hashlib
import os
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from core.attribution.evidence import (
    AttributionState,
    EvidenceFamily,
    EvidenceSource,
    EvidenceConfidenceLevel,
    TargetBinding,
    EvidenceBundle,
    WatermarkObservation,
    TraceabilityObservation,
    ProvenanceObservation,
    LedgerObservation,
    IntegrityObservation,
    AttackContextObservation,
    LineageObservation,
    ExternalTelemetryObservation,
    DeviceAttestationObservation,
)
from core.calibration.models import (
    PopulationCategory,
    DatasetSplit,
    ForensicGroundTruth,
    ForensicSampleRecord,
)


class ForensicCorporaBuilder:
    """
    Generates standardized evaluation populations (A through L) with ground-truth labels.
    Guarantees strict separation across dataset partitions.
    """

    def __init__(self, random_seed: int = 26237):
        self.random_seed = random_seed
        self.rng = np.random.RandomState(random_seed)

    def _make_binding(self, doc_id: str, rel_id: str, carrier_hash: Optional[str] = None) -> TargetBinding:
        c_hash = carrier_hash or hashlib.sha256(f"{doc_id}:{rel_id}".encode()).hexdigest()
        return TargetBinding(
            document_id=doc_id,
            release_id=rel_id,
            artifact_hash=c_hash,
            document_root_hash=hashlib.sha256(doc_id.encode()).hexdigest()
        )

    def generate_population_sample(
        self,
        category: PopulationCategory,
        sample_index: int,
        split: DatasetSplit
    ) -> ForensicSampleRecord:
        """Generates a single synthetic forensic evaluation sample for a given population and split."""
        sample_id = f"smp_{split.value.lower()}_{category.value[:3].lower()}_{sample_index:04d}"
        doc_id = f"doc_{split.value.lower()}_{sample_index:04d}"
        rel_id = f"rel_{split.value.lower()}_{sample_index:04d}"
        rec_alice = f"rec_alice_{sample_index:04d}"
        rec_bob = f"rec_bob_{sample_index:04d}"

        binding = self._make_binding(doc_id, rel_id)

        # Build category-specific evidence bundles and ground truths
        if category == PopulationCategory.POSITIVE_CORRECT:
            # High-confidence multi-channel match for Alice
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    ProvenanceObservation(
                        source_id=f"prov_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 7.0},
                        is_valid=True,
                        log_likelihood_ratio=7.0,
                        algorithm="ML-DSA-65",
                        signature_valid=True,
                        signer_recipient_id=rec_alice
                    ),
                    LedgerObservation(
                        source_id=f"ledger_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 4.0},
                        is_valid=True,
                        log_likelihood_ratio=4.0,
                        chain_valid=True,
                        matching_events_count=1
                    ),
                    WatermarkObservation(
                        source_id=f"wm_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 5.0},
                        is_valid=True,
                        log_likelihood_ratio=5.0,
                        bit_error_rate=0.02
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=rec_alice,
                is_attributable=True,
                expected_state=AttributionState.ATTRIBUTED,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash
            )

        elif category == PopulationCategory.NEGATIVE_CLEAN:
            # Completely clean unwatermarked carrier -> NO_SIGNAL
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=None,
                is_attributable=False,
                expected_state=AttributionState.NO_SIGNAL,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash
            )

        elif category == PopulationCategory.WRONG_RECIPIENT:
            # Forged/tampered marker claiming unknown recipient with invalid signature
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    ProvenanceObservation(
                        source_id=f"prov_{sample_id}",
                        target_binding=binding,
                        primary_candidate="rec_unregistered_intruder",
                        candidate_scores={"rec_unregistered_intruder": 0.0},
                        is_valid=False,  # Signature verification fails
                        log_likelihood_ratio=0.0,
                        algorithm="ML-DSA-65",
                        signature_valid=False,
                        signer_recipient_id="rec_unregistered_intruder"
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=None,
                is_attributable=False,
                expected_state=AttributionState.INSUFFICIENT_EVIDENCE,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash,
                is_adversarial=True
            )

        elif category == PopulationCategory.WRONG_DOCUMENT:
            # Marker from Doc X transplanted into Doc Y
            other_binding = self._make_binding(f"doc_foreign_{sample_index:04d}", "rel_foreign_001")
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    WatermarkObservation(
                        source_id=f"wm_transplant_{sample_id}",
                        target_binding=other_binding,  # Mismatched target binding
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 4.0},
                        is_valid=True,
                        log_likelihood_ratio=4.0
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=None,
                is_attributable=False,
                expected_state=AttributionState.CONFLICT,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash,
                is_adversarial=True
            )

        elif category == PopulationCategory.TAMPERED_ARTIFACT:
            # High bit corruption / destroyed ECC
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    WatermarkObservation(
                        source_id=f"wm_corrupt_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 0.0},
                        is_valid=False,
                        log_likelihood_ratio=0.0,
                        bit_error_rate=0.48
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=None,
                is_attributable=False,
                expected_state=AttributionState.INSUFFICIENT_EVIDENCE,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash
            )

        elif category == PopulationCategory.REPLAYED_EVIDENCE:
            # Old timestamp / replayed nonce
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    IntegrityObservation(
                        source_id=f"integ_replay_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 0.0},
                        is_valid=False,
                        log_likelihood_ratio=0.0,
                        hash_match=False
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=None,
                is_attributable=False,
                expected_state=AttributionState.CONFLICT,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash,
                is_adversarial=True
            )

        elif category == PopulationCategory.CONFLICTING_EVIDENCE:
            # Tardos says Alice, Watermark says Bob
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    ProvenanceObservation(
                        source_id=f"prov_alice_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 7.0},
                        is_valid=True,
                        log_likelihood_ratio=7.0,
                        algorithm="ML-DSA-65",
                        signature_valid=True,
                        signer_recipient_id=rec_alice
                    ),
                    WatermarkObservation(
                        source_id=f"wm_bob_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_bob,
                        candidate_scores={rec_bob: 6.5},
                        is_valid=True,
                        log_likelihood_ratio=6.5
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=None,
                is_attributable=False,
                expected_state=AttributionState.CONFLICT,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash,
                is_adversarial=True
            )

        elif category == PopulationCategory.INSUFFICIENT_EVIDENCE:
            # Weak marginal observation below decision threshold
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    WatermarkObservation(
                        source_id=f"wm_weak_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 2.0},
                        is_valid=True,
                        log_likelihood_ratio=2.0  # Below min_attribution_score 6.0
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=None,
                is_attributable=False,
                expected_state=AttributionState.INSUFFICIENT_EVIDENCE,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash
            )

        elif category == PopulationCategory.UNKNOWN_DOWNSTREAM:
            # Proven decryption by Alice, then unmonitored downstream hop -> LAST_KNOWN_HOLDER
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    ProvenanceObservation(
                        source_id=f"prov_root_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 8.0},
                        is_valid=True,
                        log_likelihood_ratio=8.0,
                        algorithm="ML-DSA-65",
                        signature_valid=True,
                        signer_recipient_id=rec_alice
                    ),
                    LineageObservation(
                        source_id=f"lineage_gap_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 3.0},
                        is_valid=True,
                        log_likelihood_ratio=3.0,
                        lineage_depth=3,
                        is_lineage_valid=True,
                        last_known_holder=rec_alice
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=rec_alice,  # Proven decryption event
                is_attributable=True,
                expected_state=AttributionState.ATTRIBUTED,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash,
                metadata={"honesty_boundary": "LAST_KNOWN_HOLDER"}
            )

        elif category == PopulationCategory.ACCOUNT_DEVICE_MISMATCH:
            # Alice's account accessed from Bob's enrolled device
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    ProvenanceObservation(
                        source_id=f"prov_acc_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 6.5},
                        is_valid=True,
                        log_likelihood_ratio=6.5,
                        algorithm="ML-DSA-65",
                        signature_valid=True,
                        signer_recipient_id=rec_alice
                    ),
                    DeviceAttestationObservation(
                        source_id=f"dev_att_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_bob,
                        candidate_scores={rec_bob: 3.0},
                        device_id="dev_bob_workstation",
                        is_valid=True,
                        log_likelihood_ratio=3.0
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=rec_alice,
                is_attributable=True,
                expected_state=AttributionState.ATTRIBUTED,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash,
                metadata={"compromise_flag": "DEVICE_MISMATCH"}
            )

        elif category == PopulationCategory.TELEMETRY_GAP:
            # Valid crypto and watermark, but telemetry system dropped packets
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    ProvenanceObservation(
                        source_id=f"prov_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 7.0},
                        is_valid=True,
                        log_likelihood_ratio=7.0,
                        algorithm="ML-DSA-65",
                        signature_valid=True,
                        signer_recipient_id=rec_alice
                    ),
                    WatermarkObservation(
                        source_id=f"wm_{sample_id}",
                        target_binding=binding,
                        primary_candidate=rec_alice,
                        candidate_scores={rec_alice: 5.0},
                        is_valid=True,
                        log_likelihood_ratio=5.0
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=rec_alice,
                is_attributable=True,
                expected_state=AttributionState.ATTRIBUTED,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash
            )

        else:  # OUT_OF_ENVELOPE
            # Severe distortion beyond calibration range
            bundle = EvidenceBundle(
                target_binding=binding,
                observations=[
                    AttackContextObservation(
                        source_id=f"att_extreme_{sample_id}",
                        target_binding=binding,
                        is_valid=True,
                        log_likelihood_ratio=0.0,
                        crop_ratio=0.10,  # 90% cropped
                        rotation_degrees=43.5,
                        noise_level=80.0
                    )
                ]
            )
            gt = ForensicGroundTruth(
                sample_id=sample_id,
                split=split,
                population=category,
                true_recipient_id=None,
                is_attributable=False,
                expected_state=AttributionState.NO_SIGNAL,
                document_id=doc_id,
                release_id=rel_id,
                content_hash=binding.artifact_hash
            )

        return ForensicSampleRecord(
            sample_id=sample_id,
            ground_truth=gt,
            evidence_bundle=bundle,
            carrier_bytes_hash=binding.artifact_hash
        )

    def generate_full_evaluation_corpus(
        self,
        samples_per_category: int = 100
    ) -> Dict[DatasetSplit, List[ForensicSampleRecord]]:
        """
        Generates full corpus partitioned into CALIBRATION (50%), VALIDATION (25%), and HELD_OUT_TEST (25%).
        """
        splits_corpus: Dict[DatasetSplit, List[ForensicSampleRecord]] = {
            DatasetSplit.CALIBRATION: [],
            DatasetSplit.VALIDATION: [],
            DatasetSplit.HELD_OUT_TEST: []
        }

        calib_count = int(samples_per_category * 0.50)
        val_count = int(samples_per_category * 0.25)
        test_count = samples_per_category - calib_count - val_count

        for cat in PopulationCategory:
            # 1. Calibration Split
            for i in range(calib_count):
                rec = self.generate_population_sample(cat, i, DatasetSplit.CALIBRATION)
                splits_corpus[DatasetSplit.CALIBRATION].append(rec)

            # 2. Validation Split
            for i in range(calib_count, calib_count + val_count):
                rec = self.generate_population_sample(cat, i, DatasetSplit.VALIDATION)
                splits_corpus[DatasetSplit.VALIDATION].append(rec)

            # 3. Held-out Test Split
            for i in range(calib_count + val_count, samples_per_category):
                rec = self.generate_population_sample(cat, i, DatasetSplit.HELD_OUT_TEST)
                splits_corpus[DatasetSplit.HELD_OUT_TEST].append(rec)

        return splits_corpus
