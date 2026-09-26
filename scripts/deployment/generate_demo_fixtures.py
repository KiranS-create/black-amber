import base64
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from demo.end_to_end import create_sample_pdf
from core.recipient import RecipientRegistry, default_registry
from core.release import ReleaseManager, default_release_manager
from core.provenance.decryption import RecipientDecryptionClient, default_decryption_client
from core.ledger.ledger import TamperEvidentLedger, default_ledger
from core.traceability.provider import PrototypeTraceabilityProvider
from core.attribution.engine import AttributionEngine, AttributionState, default_attribution_engine

def generate_fixtures(
    output_dir: Optional[Path] = None,
    use_default_singletons: bool = True
) -> dict:
    fixtures_dir = output_dir or (PROJECT_ROOT / "data" / "demo_fixtures")
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] Generating deterministic demo fixtures in: {fixtures_dir}")

    # 1. Initialize subsystems
    if use_default_singletons:
        registry = default_registry
        ledger = default_ledger
        provider = PrototypeTraceabilityProvider()
        release_mgr = default_release_manager
        decrypt_client = default_decryption_client
        engine = default_attribution_engine
    else:
        registry = RecipientRegistry()
        ledger = TamperEvidentLedger()
        provider = PrototypeTraceabilityProvider()
        release_mgr = ReleaseManager(registry=registry)
        decrypt_client = RecipientDecryptionClient(ledger=ledger, traceability_provider=provider)
        engine = AttributionEngine(traceability_provider=provider, ledger=ledger, registry=registry)

    # 2. Master Document
    sample_pdf_bytes = create_sample_pdf("TOP SECRET OPERATION SIH26237 - STRATEGIC DIRECTIVE")
    source_pdf_path = fixtures_dir / "source_document.pdf"
    with open(source_pdf_path, "wb") as f:
        f.write(sample_pdf_bytes)
    doc_hash = hashlib.sha256(sample_pdf_bytes).hexdigest()
    print(f"[+] Master Document: {source_pdf_path.name} (SHA-256: {doc_hash[:16]}...)")

    # 3. Enroll Recipients
    alice = registry.enroll("Alice", "alice")
    bob = registry.enroll("Bob", "bob")
    charlie = registry.enroll("Charlie", "charlie")

    recipients_meta = [
        alice.to_public().model_dump(),
        bob.to_public().model_dump(),
        charlie.to_public().model_dump()
    ]
    with open(fixtures_dir / "recipients.json", "w") as f:
        json.dump(recipients_meta, f, indent=2)

    # 4. Create Multi-Recipient Release
    release = release_mgr.create_release(
        document_bytes=sample_pdf_bytes,
        document_name="source_document.pdf",
        issuer_id="HQ_COMMAND",
        recipient_ids=["alice", "bob", "charlie"]
    )
    with open(fixtures_dir / "release.json", "w") as f:
        json.dump(release.model_dump(), f, indent=2)

    # 5. Bob Decrypts and Signs Provenance Event
    bob_pkg = release.packages["bob"]
    _, bob_traceable_bytes, bob_event, bob_event_hash = decrypt_client.decrypt_package(
        package=bob_pkg,
        recipient=bob
    )
    bob_traceable_path = fixtures_dir / "bob_traceable.pdf"
    with open(bob_traceable_path, "wb") as f:
        f.write(bob_traceable_bytes)
    bob_traceable_hash = hashlib.sha256(bob_traceable_bytes).hexdigest()

    # 6. Bob Leak (Standard Attributable Scenario)
    bob_leak_path = fixtures_dir / "bob_leak.pdf"
    with open(bob_leak_path, "wb") as f:
        f.write(bob_traceable_bytes)

    # 7. Tampered Marker Leak (Insufficient Evidence Scenario)
    tampered_bytes = bob_traceable_bytes.replace(
        b"SIH26237-TRACEABILITY-MARKER-START",
        b"CORRUPTED-MARKER-HEADER-XXXX"
    )
    tampered_leak_path = fixtures_dir / "tampered_leak.pdf"
    with open(tampered_leak_path, "wb") as f:
        f.write(tampered_bytes)

    # 8. Clean Unmarked Document (No Signal Scenario)
    clean_path = fixtures_dir / "clean_document.pdf"
    with open(clean_path, "wb") as f:
        f.write(sample_pdf_bytes)

    # 9. Verify expected attribution states
    res_bob = engine.analyze_leak(bob_traceable_bytes, expected_release_id=release.release_id)
    assert res_bob.state == AttributionState.ATTRIBUTED
    assert res_bob.candidate.recipient_id == "bob"

    res_tamper = engine.analyze_leak(tampered_bytes, expected_release_id=release.release_id)
    assert res_tamper.state in (AttributionState.NO_SIGNAL, AttributionState.INSUFFICIENT_EVIDENCE)
    assert res_tamper.should_abstain is True

    res_clean = engine.analyze_leak(sample_pdf_bytes)
    assert res_clean.state == AttributionState.NO_SIGNAL
    assert res_clean.should_abstain is True

    # 10. Write Manifest
    manifest = {
        "version": "1.0.0",
        "generated_at": release.created_at,
        "master_document": {
            "filename": "source_document.pdf",
            "sha256": doc_hash,
            "size_bytes": len(sample_pdf_bytes)
        },
        "release": {
            "release_id": release.release_id,
            "document_id": release.document_id,
            "recipient_ids": ["alice", "bob", "charlie"]
        },
        "fixtures": [
            {
                "file": "bob_leak.pdf",
                "sha256": bob_traceable_hash,
                "description": "Legitimate intercepted leak from recipient Bob",
                "expected_state": "ATTRIBUTED",
                "expected_candidate": "bob",
                "expected_confidence": "HIGH"
            },
            {
                "file": "tampered_leak.pdf",
                "sha256": hashlib.sha256(tampered_bytes).hexdigest(),
                "description": "Carrier artifact with corrupted marker header",
                "expected_state": "NO_SIGNAL",
                "expected_candidate": None,
                "should_abstain": True
            },
            {
                "file": "clean_document.pdf",
                "sha256": doc_hash,
                "description": "Pristine document with no embedded traceability marker",
                "expected_state": "NO_SIGNAL",
                "expected_candidate": None,
                "should_abstain": True
            }
        ]
    }
    manifest_path = fixtures_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] Demo Fixture Generation Complete! Manifest written to: {manifest_path.name}\n")
    return manifest

if __name__ == "__main__":
    from typing import Optional
    generate_fixtures()
