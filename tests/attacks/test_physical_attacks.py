import pytest
from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.physical.simulation import PrintCameraSimulationAttack
from attacks.physical.capture import PhysicalArtifactCaptureImporter, PhysicalCaptureMetadata

@pytest.fixture
def highres_img_bytes():
    return BaselineTestCorpus.generate_high_res_page_image()

def test_print_camera_simulation_execution_and_tag(highres_img_bytes):
    sim_attack = PrintCameraSimulationAttack()
    res = sim_attack.apply(highres_img_bytes, seed=42)

    assert res.success is True
    assert res.physical_or_simulated == "SIMULATED"
    assert res.attack_family == "PRINT_CAMERA"
    assert res.attack_name == "print_camera_simulation"
    assert res.output_type == "IMAGE_JPEG"
    assert res.metrics is not None
    assert res.metrics.psnr is not None
    assert res.metrics.ssim is not None

def test_print_camera_simulation_reproducibility(highres_img_bytes):
    sim_attack = PrintCameraSimulationAttack()
    res1 = sim_attack.apply(highres_img_bytes, seed=12345)
    res2 = sim_attack.apply(highres_img_bytes, seed=12345)
    assert res1.output_hash == res2.output_hash, "Identical seed must produce identical simulation output"

    res3 = sim_attack.apply(highres_img_bytes, seed=54321)
    assert res1.output_hash != res3.output_hash, "Different seeds must produce different simulation output"

def test_physical_capture_importer_metadata_and_tag(highres_img_bytes):
    importer = PhysicalArtifactCaptureImporter()
    meta = PhysicalCaptureMetadata(
        printer_model="HP LaserJet Enterprise M608",
        paper_type="A4 80gsm Recycled",
        camera_device="Apple iPhone 15 Pro",
        lighting_condition="Diffused Fluorescent 4000K",
        capture_distance_cm=40.0,
        capture_angle_deg=20.0,
        notes="Authentic physical print-and-scan test vector"
    )

    res = importer.import_physical_capture(
        captured_artifact_bytes=highres_img_bytes,
        original_artifact_bytes=highres_img_bytes,
        telemetry=meta
    )

    assert res.success is True
    assert res.physical_or_simulated == "PHYSICAL"
    assert res.attack_family == "PRINT_CAMERA"
    assert res.parameters["printer_model"] == "HP LaserJet Enterprise M608"
    assert res.parameters["camera_device"] == "Apple iPhone 15 Pro"
    assert res.notes == "Authentic physical print-and-scan test vector"
