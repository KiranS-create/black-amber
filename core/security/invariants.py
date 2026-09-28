"""
core/security/invariants.py

Formal Security Invariant Catalog and Verification Specifications for AegisTrace.
Defines the 12 Golden Security Invariants and formal system rules across:
Cryptography, Identity, Key Lifecycle, Watermark, Ledger, Lineage, Telemetry,
Attribution, Evidence Packaging, and Air-Gap Enforcement.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


class InvariantDomain(str, Enum):
    CRYPTOGRAPHY = "CRYPTOGRAPHY"
    IDENTITY = "IDENTITY"
    KEY_LIFECYCLE = "KEY_LIFECYCLE"
    WATERMARK = "WATERMARK"
    LEDGER = "LEDGER"
    LINEAGE = "LINEAGE"
    TELEMETRY = "TELEMETRY"
    ATTRIBUTION = "ATTRIBUTION"
    EVIDENCE_PACKAGE = "EVIDENCE_PACKAGE"
    AIR_GAP = "AIR_GAP"


@dataclass(frozen=True)
class SecurityInvariant:
    invariant_id: str
    domain: InvariantDomain
    title: str
    formal_statement: str
    threat_mitigated: str
    enforcing_module: str
    test_suite_reference: str
    is_golden: bool = False


# ==============================================================================
# 12 GOLDEN SECURITY INVARIANTS (MUST NEVER FAIL)
# ==============================================================================

GOLDEN_INVARIANTS: List[SecurityInvariant] = [
    SecurityInvariant(
        invariant_id="INVARIANT-001",
        domain=InvariantDomain.IDENTITY,
        title="Cross-Tenant Evidence Isolation",
        formal_statement="An evidence object belonging to Tenant A must never verify or be queried within Tenant B's boundary under any query path.",
        threat_mitigated="Cross-tenant leakage, horizontal privilege escalation, evidence injection.",
        enforcing_module="core.evidence_package.verifier, apps.api.security",
        test_suite_reference="tests/properties/test_tenant_and_api_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-002",
        domain=InvariantDomain.KEY_LIFECYCLE,
        title="Revoked Key Authorization Prohibition",
        formal_statement="A cryptographic key in state REVOKED or COMPROMISED must strictly fail-closed if used to authorize new events or transitions.",
        threat_mitigated="Unauthorized usage of revoked credentials, zombie key abuse.",
        enforcing_module="core.crypto.lifecycle.state_machine, core.crypto.lifecycle.manager",
        test_suite_reference="tests/properties/test_key_lifecycle_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-003",
        domain=InvariantDomain.KEY_LIFECYCLE,
        title="Historical Signature Continuous Verifiability",
        formal_statement="Cryptographic signatures generated when a key was ACTIVE must remain verifiable indefinitely, even after subsequent key rotation or retirement.",
        threat_mitigated="Post-rotation audit trail repudiation, broken historical forensics.",
        enforcing_module="core.crypto.lifecycle.resolver, core.crypto.signatures",
        test_suite_reference="tests/properties/test_key_lifecycle_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-004",
        domain=InvariantDomain.LEDGER,
        title="Ledger Hash Chain Tamper Sensitivity",
        formal_statement="Any bitwise modification, reordering, deletion, or insertion in a ledger event chain must cause verify_chain() to fail or return an explicit conflict state.",
        threat_mitigated="Silent ledger tampering, covert evidence removal, audit spoofing.",
        enforcing_module="core.ledger.ledger.TamperEvidentLedger",
        test_suite_reference="tests/properties/test_ledger_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-005",
        domain=InvariantDomain.EVIDENCE_PACKAGE,
        title="Evidence Package Merkle & Content Integrity",
        formal_statement="An evidence package must fail verification if any committed object, manifest hash, or digital signature is altered or substituted.",
        threat_mitigated="Evidence tampering, malicious report forgery, chain-of-custody poisoning.",
        enforcing_module="core.evidence_package.verifier.EvidencePackageVerifier",
        test_suite_reference="tests/properties/test_evidence_package_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-006",
        domain=InvariantDomain.WATERMARK,
        title="Watermark Cryptographic Context Binding",
        formal_statement="A watermark token extracted from Document X or Session S must fail verification if evaluated against any other document ID or session context.",
        threat_mitigated="Watermark replay attacks, cross-document framing, forensic collusion.",
        enforcing_module="core.watermark, core.traceability.provider",
        test_suite_reference="tests/properties/test_watermark_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-007",
        domain=InvariantDomain.ATTRIBUTION,
        title="Insufficient Evidence Mandatory Abstention",
        formal_statement="When forensic signals are weak, missing, uncorroborated, or conflicting, the attribution engine must strictly abstain (NO_SIGNAL, INSUFFICIENT_EVIDENCE, CONFLICT, ABSTAINED) and must never emit ATTRIBUTED.",
        threat_mitigated="False positive attribution, wrongful accusation, ungrounded forensic speculation.",
        enforcing_module="core.attribution.engine, core.attribution.policy",
        test_suite_reference="tests/properties/test_attribution_and_abstention_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-008",
        domain=InvariantDomain.LINEAGE,
        title="Downstream Lineage Transition Anti-Fabrication",
        formal_statement="Lineage traversal must never invent missing ancestors or bridge unverified hops; missing parents must remain explicit boundaries.",
        threat_mitigated="Fabricated provenance paths, phantom forwarding claims, broken causality.",
        enforcing_module="core.lineage.verification, core.lineage.service",
        test_suite_reference="tests/properties/test_lineage_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-009",
        domain=InvariantDomain.AIR_GAP,
        title="Air-Gap Non-Loopback Egress Prohibition",
        formal_statement="When AEGISTRACE_AIRGAP_MODE is active, all socket connect and DNS getaddrinfo requests to non-loopback destinations must be intercepted and rejected with AirgapViolationError.",
        threat_mitigated="Covert external telemetry exfiltration, phone-home data leaks in classified enclaves.",
        enforcing_module="core.security.airgap.NetworkEgressGuard",
        test_suite_reference="tests/properties/test_airgap_and_concurrency_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-010",
        domain=InvariantDomain.CRYPTOGRAPHY,
        title="Post-Quantum Signature Unforgeability",
        formal_statement="An ML-DSA-65 signature generated under public key PK must verify if and only if generated with matching private key SK over the exact message bytes.",
        threat_mitigated="Signature spoofing, identity impersonation, forged receipts.",
        enforcing_module="core.crypto.signatures.MLDSA65",
        test_suite_reference="tests/properties/test_crypto_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-011",
        domain=InvariantDomain.IDENTITY,
        title="Foreign-Tenant ID Substitution Neutralization",
        formal_statement="Substituting an ID from Tenant A into Tenant B's request context must cause the request to be rejected with 403 Forbidden or 404 Not Found.",
        threat_mitigated="IDOR, object reference substitution, broken access control.",
        enforcing_module="apps.api.security, apps.api.orchestrator",
        test_suite_reference="tests/properties/test_tenant_and_api_properties.py",
        is_golden=True,
    ),
    SecurityInvariant(
        invariant_id="INVARIANT-012",
        domain=InvariantDomain.LEDGER,
        title="Stale State Recovery Authoritative Rejection",
        formal_statement="Restoration of an older ledger backup or stale snapshot must be detected as non-authoritative when compared against verifiable checkpoints.",
        threat_mitigated="Rollback attacks, state rewinding, ledger resurrection.",
        enforcing_module="core.recovery.ledger_recovery, core.deployment.upgrade",
        test_suite_reference="tests/properties/test_ledger_properties.py",
        is_golden=True,
    ),
]


# Map invariant ID to definition
SECURITY_INVARIANTS_CATALOG: Dict[str, SecurityInvariant] = {
    inv.invariant_id: inv for inv in GOLDEN_INVARIANTS
}


def assert_invariant(
    condition: bool,
    invariant_id: str,
    details: str,
    seed: Optional[int] = None,
    counterexample: Any = None,
) -> None:
    """Helper to assert security invariant and raise typed InvariantViolation."""
    if not condition:
        from core.testing.property_engine import InvariantViolation
        inv = SECURITY_INVARIANTS_CATALOG.get(invariant_id)
        title = inv.title if inv else "Security Invariant"
        msg = f"{title} [{invariant_id}]: {details}"
        raise InvariantViolation(invariant_id, msg, seed=seed, counterexample=counterexample)
