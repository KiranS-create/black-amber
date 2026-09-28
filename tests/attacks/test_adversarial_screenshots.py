import io
import pytest
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.digital.image_attacks import (
    ScreenshotSimulationAttack,
    CropAttack,
    PartialCropAttack,
    ResizeAttack,
    JpegRecompressionAttack,
    PngConversionAttack,
    bytes_to_pil,
    pil_to_bytes,
)
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger
from core.attribution.engine import AttributionEngine, AttributionState

@pytest.fixture
def screenshot_env():
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
        document_name="screen_test.pdf",
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
    }

def test_screenshot_simulation_image_metrics(screenshot_env):
    env = screenshot_env
    attack = ScreenshotSimulationAttack()
    res = attack.apply(env["high_res_page"], {"device_scale": 0.85, "display_gamma": 1.1, "add_border": True}, seed=42)

    assert res.success is True
    assert res.output_type == "IMAGE_PNG"
    assert res.metrics.psnr is not None
    assert res.metrics.ssim is not None
    assert res.metrics.ssim > 0.60

def test_screenshot_cropped_active_window(screenshot_env):
    env = screenshot_env
    sim = ScreenshotSimulationAttack()
    shot_bytes = sim._execute_transform(env["high_res_page"], {"device_scale": 0.9, "add_border": True}, seed=42).artifact_bytes

    # Crop active inner window
    crop_atk = CropAttack()
    cropped = crop_atk._execute_transform(shot_bytes, {"crop_fraction": 0.1, "anchor": "center"}, seed=42).artifact_bytes

    assert len(cropped) > 0
    img = bytes_to_pil(cropped)
    assert img.width > 0 and img.height > 0

def test_screenshot_recompressed_jpeg_sweep(screenshot_env):
    env = screenshot_env
    sim = ScreenshotSimulationAttack()
    shot_bytes = sim._execute_transform(env["high_res_page"], {"device_scale": 0.9, "add_border": False}, seed=42).artifact_bytes

    for quality in [90, 75, 50, 20]:
        jpeg_atk = JpegRecompressionAttack()
        res = jpeg_atk.apply(shot_bytes, {"quality": quality}, seed=42)
        assert res.success is True
        assert res.metrics.ssim > 0.50

def test_screenshot_format_roundtrip_png_jpeg_png(screenshot_env):
    env = screenshot_env
    orig = env["high_res_page"]

    # PNG -> JPEG (Q=80) -> PNG
    jpeg_atk = JpegRecompressionAttack()
    jpg_bytes = jpeg_atk._execute_transform(orig, {"quality": 80}, seed=42).artifact_bytes
    png_atk = PngConversionAttack()
    png_bytes = png_atk._execute_transform(jpg_bytes, {}, seed=42).artifact_bytes

    img = bytes_to_pil(png_bytes)
    assert img.format == "PNG"

def test_pdf_reconstruction_from_screenshot_fails_closed_safely(screenshot_env):
    env = screenshot_env
    # Take screenshot of page and rebuild PDF around image
    img = bytes_to_pil(env["high_res_page"])
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)
    c.drawImage(ImageReader(img_buf), 0, 0, width=letter[0], height=letter[1])
    c.showPage()
    c.save()
    reconstructed_pdf = buf.getvalue()

    # Evaluating reconstructed raster PDF against structural marker engine
    res = env["engine"].analyze_leak(reconstructed_pdf, expected_release_id=env["release"].release_id)
    # Must fail-closed without false attribution
    assert res.state == AttributionState.NO_SIGNAL
    assert res.should_abstain is True
    assert res.candidate is None

def test_double_rasterization_preserves_safety(screenshot_env):
    env = screenshot_env
    # First rasterization
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    buf1 = io.BytesIO()
    img.save(buf1, format="PNG")

    # Re-wrap
    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=letter)
    buf1.seek(0)
    c.drawImage(ImageReader(buf1), 0, 0, width=letter[0], height=letter[1])
    c.showPage()
    c.save()
    re_rasterized = pdf_buf.getvalue()

    res = env["engine"].analyze_leak(re_rasterized, expected_release_id=env["release"].release_id)
    assert res.state == AttributionState.NO_SIGNAL
    assert res.should_abstain is True
