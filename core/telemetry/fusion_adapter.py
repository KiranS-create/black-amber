"""
AegisTrace Telemetry Evidence Fusion Adapter.

Bridges external operational telemetry correlation results into the core
EvidenceFusionEngine and EvidenceBundle model.
"""

from typing import Dict, Any, Optional, Tuple, List

from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceFamily,
    DependencyType,
    ExternalTelemetryObservation,
    TargetBinding,
)
from core.telemetry.engine import (
    TelemetryAttributionReport,
    TelemetryAttributionState,
    CandidateAttributionType,
)


class TelemetryFusionAdapter:
    """
    Translates a TelemetryAttributionReport into an ExternalTelemetryObservation
    and attaches it to an EvidenceBundle with strict boundary preservation.
    """

    @staticmethod
    def report_to_observation(
        report: TelemetryAttributionReport,
        target_binding: Optional[TargetBinding] = None,
    ) -> ExternalTelemetryObservation:
        """
        Convert report to ExternalTelemetryObservation.
        """
        # Determine LLR (Log-Likelihood Ratio) based on primary state
        # In forensic evaluation:
        # HUMAN_ATTRIBUTION_CORROBORATED -> High positive LLR
        # LAST_KNOWN_CONTROLLED_HOLDER -> Moderate LLR for original, neutral for downstream
        # ABSTAINED / CONFLICT -> 0.0 or negative (fail-closed)
        if report.primary_state == TelemetryAttributionState.ABSTAINED:
            llr = 0.0
            reliability = 0.0
        elif report.primary_state == TelemetryAttributionState.HUMAN_ATTRIBUTION_CORROBORATED:
            llr = 4.5
            reliability = 0.95
        elif report.primary_state == TelemetryAttributionState.PUBLICATION_EVENT_IDENTIFIED:
            llr = 3.5
            reliability = 0.88
        elif report.primary_state == TelemetryAttributionState.LAST_KNOWN_CONTROLLED_HOLDER:
            llr = 2.5
            reliability = 0.80
        elif report.primary_state == TelemetryAttributionState.DOWNSTREAM_DEVICE_IDENTIFIED:
            llr = 3.0
            reliability = 0.85
        elif report.primary_state == TelemetryAttributionState.ORIGINAL_RECIPIENT_IDENTIFIED:
            llr = 2.0
            reliability = 0.90
        else:
            llr = 0.0
            reliability = 0.50

        # Candidate scores mapping
        scores = {}
        for cand in report.candidates:
            if cand.candidate_type == CandidateAttributionType.CORROBORATED_HUMAN:
                scores[cand.candidate_id] = 4.5 * cand.confidence
            elif cand.candidate_type == CandidateAttributionType.OBSERVED_ACCOUNT:
                scores[cand.candidate_id] = 2.5 * cand.confidence
            elif cand.candidate_type == CandidateAttributionType.OBSERVED_DEVICE:
                scores[cand.candidate_id] = 2.0 * cand.confidence

        primary_cand = report.last_known_controlled_holder or report.original_recipient_id

        obs = ExternalTelemetryObservation(
            source_id=f"telemetry-{report.report_id}",
            family=EvidenceFamily.EXTERNAL_TELEMETRY,
            dependency_type=DependencyType.INDEPENDENT,
            title="External Telemetry Correlation Observation",
            is_valid=(report.primary_state != TelemetryAttributionState.ABSTAINED),
            log_likelihood_ratio=llr,
            candidate_scores=scores,
            primary_candidate=primary_cand,
            reliability_prior=reliability,
            effective_reliability=reliability,
            target_binding=target_binding or TargetBinding(),
            primary_state=report.primary_state.value,
            last_known_controlled_holder=report.last_known_controlled_holder,
            downstream_holder_account=report.downstream_holder_account,
            downstream_device_id=report.downstream_device_id,
            publication_source=report.publication_source,
            account_compromised_or_shared=report.account_compromised_or_shared,
            is_human_corroborated=(report.primary_state == TelemetryAttributionState.HUMAN_ATTRIBUTION_CORROBORATED),
            observed_events_count=len(report.timeline),
            custody_gaps_count=len(report.custody_gaps),
            boundary_statement=report.boundary_statement,
            details={
                "all_states": [s.value for s in report.all_states],
                "summary_verdict": report.summary_verdict,
                "custody_gaps": report.custody_gaps,
            },
        )
        return obs

    @classmethod
    def attach_to_bundle(
        cls,
        bundle: EvidenceBundle,
        report: TelemetryAttributionReport,
    ) -> None:
        """
        Attaches the telemetry observation to an existing EvidenceBundle.
        """
        obs = cls.report_to_observation(report, target_binding=bundle.target_binding)
        bundle.add_observation(obs)

    @classmethod
    def custody_report_to_observations(
        cls,
        report: Any,  # CustodyTimelineReport
        target_binding: Optional[TargetBinding] = None,
    ) -> Tuple[ExternalTelemetryObservation, Optional[Any]]:
        """
        Translates a unified CustodyTimelineReport into an ExternalTelemetryObservation
        and an optional DeviceAttestationObservation.
        Enforces exact-copy downstream boundary: if UNKNOWN_DOWNSTREAM_ACTOR,
        abstains from accusing the last known holder.
        """
        from core.lineage.models import ForensicBoundaryState
        from core.attribution.evidence import DeviceAttestationObservation

        # Fail-closed checks
        if report.should_abstain or report.account_compromised_or_shared or report.forensic_boundary_state == ForensicBoundaryState.CONFLICT:
            llr = 0.0
            reliability = 0.0
            is_valid = False
        elif report.forensic_boundary_state == ForensicBoundaryState.UNKNOWN_DOWNSTREAM_ACTOR:
            # Exact-copy downstream boundary: do NOT accuse last known holder of publishing
            llr = 0.0
            reliability = 0.50
            is_valid = True
        elif report.confirmed_publisher_id:
            llr = 4.5
            reliability = 0.95
            is_valid = True
        elif report.last_known_controlled_holder:
            llr = 2.5
            reliability = 0.85
            is_valid = True
        else:
            llr = 0.0
            reliability = 0.50
            is_valid = False

        scores = {}
        if report.confirmed_publisher_id:
            scores[report.confirmed_publisher_id] = 4.5 * report.confidence_score
        elif report.last_known_controlled_holder and report.forensic_boundary_state != ForensicBoundaryState.UNKNOWN_DOWNSTREAM_ACTOR:
            scores[report.last_known_controlled_holder] = 2.5 * report.confidence_score
        if report.original_recipient_id:
            scores[report.original_recipient_id] = 2.0 * report.confidence_score

        primary_cand = report.confirmed_publisher_id or (
            report.last_known_controlled_holder if report.forensic_boundary_state != ForensicBoundaryState.UNKNOWN_DOWNSTREAM_ACTOR else None
        )

        dep_type = DependencyType.INDEPENDENT
        # If external observations were derived from controlled viewer or same host session, discount
        if any(item.source == "CONTROLLED_VIEWER" for item in report.timeline):
            dep_type = DependencyType.PARTIALLY_DEPENDENT

        tele_obs = ExternalTelemetryObservation(
            source_id=f"custody-telemetry-{report.report_id}",
            family=EvidenceFamily.EXTERNAL_TELEMETRY,
            dependency_type=dep_type,
            title="Unified Custody Timeline Observation",
            is_valid=is_valid,
            log_likelihood_ratio=llr,
            candidate_scores=scores,
            primary_candidate=primary_cand,
            reliability_prior=reliability,
            effective_reliability=reliability,
            target_binding=target_binding or TargetBinding(),
            primary_state=report.forensic_boundary_state.value,
            last_known_controlled_holder=report.last_known_controlled_holder,
            downstream_holder_account=report.downstream_holder_account,
            downstream_device_id=report.downstream_device_id,
            publication_source=report.publication_platform,
            account_compromised_or_shared=report.account_compromised_or_shared,
            is_human_corroborated=(report.confirmed_publisher_id is not None),
            observed_events_count=len(report.timeline),
            custody_gaps_count=len(report.custody_gaps),
            boundary_statement=report.boundary_statement,
            details={
                "causality_violations": report.causality_violations,
                "compound_actions_count": len(report.compound_actions),
                "abstention_reason": report.abstention_reason,
            },
        )

        # Optional DeviceAttestationObservation
        dev_obs = None
        devices_seen = [item.device_id for item in report.timeline if item.device_id]
        if devices_seen:
            primary_dev = devices_seen[0]
            dev_obs = DeviceAttestationObservation(
                source_id=f"device-att-{report.report_id}",
                family=EvidenceFamily.DEVICE_ATTESTATION,
                dependency_type=DependencyType.PARTIALLY_DEPENDENT,
                title="Device Attestation Observation",
                is_valid=True,
                log_likelihood_ratio=2.0 if not report.account_compromised_or_shared else 0.0,
                candidate_scores={},
                primary_candidate=None,
                target_binding=target_binding or TargetBinding(),
                device_id=primary_dev,
                attestation_state="DEVICE_ATTESTED",
                hardware_class="DEDICATED_HARDWARE_HSM",
                platform_type="TPM",
                is_hardware_attested=True,
                is_device_revoked=False,
                boundary_statement=f"Observed access bound to device '{primary_dev}'.",
            )

        return tele_obs, dev_obs

    @classmethod
    def attach_custody_report_to_bundle(
        cls,
        bundle: EvidenceBundle,
        report: Any,  # CustodyTimelineReport
    ) -> None:
        """
        Attaches the unified custody observation and optional device attestation observation to an EvidenceBundle.
        """
        tele_obs, dev_obs = cls.custody_report_to_observations(report, target_binding=bundle.target_binding)
        bundle.add_observation(tele_obs)
        if dev_obs:
            bundle.add_observation(dev_obs)
