import pytest
from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.watermark.watermark_attacks import (
    CarrierDilutionAttack,
    LocalizedBitCorruptionAttack,
    RegionReplacementAttack,
    WatermarkStrippingAttack,
    AdversarialPayloadForgeryAttack,
)
from attacks.digital.image_attacks import (
    JpegRecompressionAttack,
    ImageReEncodingAttack,
    RotationAttack,
    PerspectiveTransformAttack,
    ResizeAttack,
)
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger
from core.attribution.engine import AttributionEngine, AttributionState

@pytest.fixture
def watermark_attack_env():
    registry = RecipientRegistry()
    alice = registry.enroll("Alice", "alice")
    bob = registry.enroll("Bob", "bob")

    ledger = TamperEvidentLedger()
    trace_provider = PrototypeTraceabilityProvider()
    release_manager = ReleaseManager(registry=registry)
    decryption_client = RecipientDecryptionClient(ledger=ledger, traceability_provider=trace_provider)
    engine = AttributionEngine(traceability_provider=trace_provider, ledger=ledger, registry=registry)

    sample_doc = BaselineTestCorpus.generate_simple_text_pdf()
    release = release_manager.create_release(
        document_bytes=sample_doc,
        document_name="wm_test.pdf",
        issuer_id="HQ",
        recipient_ids=["alice", "bob"]
    )
    bob_pkg = release.packages["bob"]
    _, bob_copy, bob_event, _ = decryption_client.decrypt_package(bob_pkg, bob)
    high_res_page = BaselineTestCorpus.generate_high_res_page_image()

    return {
        "bob_copy": bob_copy,
        "high_res_page": high_res_page,
        "engine": engine,
        "release": release,
        "trace_provider": trace_provider,
    }

def test_watermark_carrier_dilution_metrics(watermark_attack_env):
    env = watermark_attack_env
    attack = CarrierDilutionAttack()
    res = attack.apply(env["high_res_page"], {"pad_factor": 1.5}, seed=42)

    assert res.success is True
    assert res.metrics.file_size_ratio > 1.0

def test_localized_bit_corruption_below_and_above_threshold(watermark_attack_env):
    env = watermark_attack_env
    attack = LocalizedBitCorruptionAttack()

    # Mild corruption (1% flips)
    res_mild = attack.apply(env["bob_copy"], {"corruption_rate": 0.01}, seed=42)
    assert res_mild.success is True

    # Severe corruption (40% flips)
    res_severe = attack.apply(env["bob_copy"], {"corruption_rate": 0.40}, seed=42)
    corrupted_bytes = attack._execute_transform(env["bob_copy"], {"corruption_rate": 0.40}, seed=42).artifact_bytes

    # Attribution engine must abstain fail-closed on severely corrupted bytes
    attr_res = env["engine"].analyze_leak(corrupted_bytes, expected_release_id=env["release"].release_id)
    assert attr_res.should_abstain is True
    assert attr_res.state in (AttributionState.INSUFFICIENT_EVIDENCE, AttributionState.NO_SIGNAL)

def test_watermark_stripping_attack_fails_closed(watermark_attack_env):
    env = watermark_attack_env
    attack = WatermarkStrippingAttack()
    stripped_bytes = attack._execute_transform(env["bob_copy"], {}, seed=42).artifact_bytes

    res = env["engine"].analyze_leak(stripped_bytes, expected_release_id=env["release"].release_id)
    assert res.state == AttributionState.NO_SIGNAL
    assert res.should_abstain is True
    assert res.candidate is None

def test_region_replacement_attack(watermark_attack_env):
    env = watermark_attack_env
    attack = RegionReplacementAttack()
    res = attack.apply(env["high_res_page"], {"region_box": (100, 100, 500, 500)}, seed=42)

    assert res.success is True
    assert res.output_type == "IMAGE_PNG"

def test_repeated_image_reencoding_cycles(watermark_attack_env):
    env = watermark_attack_env
    attack = ImageReEncodingAttack()
    res = attack.apply(env["high_res_page"], {"cycles": 5, "quality": 70}, seed=42)

    assert res.success is True
    assert res.metrics.ssim > 0.80

def test_adversarial_payload_forgery_is_never_accepted():
    """
    CRITICAL SECURITY TEST:
    An adversary attempts to forge payload bits to frame another recipient.
    Must never be accepted as valid evidence.
    """
    original_bits = [1, 0, 1, 1, 0, 0, 1, 0]
    forged_bits = AdversarialPayloadForgeryAttack.forge_payload_bits(original_bits, target_bit_index=1)

    assert forged_bits != original_bits
    assert forged_bits[1] == 1  # Flipped from 0 to 1
