import io
import pytest
from PIL import Image
from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.digital.image_attacks import (
    JpegRecompressionAttack,
    PngConversionAttack,
    QualityReductionAttack,
    ResizeAttack,
    DownscaleUpscaleAttack,
    GaussianBlurAttack,
    SharpenAttack,
    GaussianNoiseAttack,
    SaltAndPepperNoiseAttack,
    BrightnessAttack,
    ContrastAttack,
    GrayscaleConversionAttack,
    ColorSpaceConversionAttack,
    RotationAttack,
    PerspectiveTransformAttack,
    CropAttack,
    PartialCropAttack,
    ScreenshotSimulationAttack,
    ImageReEncodingAttack,
)

@pytest.fixture
def baseline_image_bytes():
    return BaselineTestCorpus.generate_high_res_page_image()

def test_all_19_image_attacks_execute_successfully(baseline_image_bytes):
    attacks = [
        (JpegRecompressionAttack(), {"quality": 70}),
        (PngConversionAttack(), {}),
        (QualityReductionAttack(), {"quality": 25}),
        (ResizeAttack(), {"scale_factor": 0.5}),
        (DownscaleUpscaleAttack(), {"factor": 0.3}),
        (GaussianBlurAttack(), {"kernel_size": 5, "sigma": 1.5}),
        (SharpenAttack(), {"strength": 1.2}),
        (GaussianNoiseAttack(), {"mean": 0.0, "std": 10.0}),
        (SaltAndPepperNoiseAttack(), {"amount": 0.01}),
        (BrightnessAttack(), {"factor": 1.1}),
        (ContrastAttack(), {"factor": 1.2}),
        (GrayscaleConversionAttack(), {}),
        (ColorSpaceConversionAttack(), {"target_space": "HSV"}),
        (RotationAttack(), {"angle": 3.0}),
        (PerspectiveTransformAttack(), {"distortion_scale": 0.04}),
        (CropAttack(), {"crop_fraction": 0.1}),
        (PartialCropAttack(), {"side": "bottom", "fraction": 0.1}),
        (ScreenshotSimulationAttack(), {"device_scale": 0.8}),
        (ImageReEncodingAttack(), {"cycles": 2, "quality": 80}),
    ]

    assert len(attacks) == 19

    for attack, params in attacks:
        result = attack.apply(baseline_image_bytes, parameters=params, seed=42)
        assert result.success is True, f"Attack {attack.ATTACK_NAME} failed: {result.observed_effect}"
        assert result.output_hash != ""
        assert result.metrics is not None
        assert result.execution_time_ms >= 0

def test_deterministic_seed_produces_identical_outputs(baseline_image_bytes):
    # Gaussian noise attack with seed
    attack = GaussianNoiseAttack()
    res1 = attack.apply(baseline_image_bytes, parameters={"std": 20.0}, seed=999)
    res2 = attack.apply(baseline_image_bytes, parameters={"std": 20.0}, seed=999)
    assert res1.output_hash == res2.output_hash, "Identical seed must yield identical output hash"

    # Different seed should yield different hash
    res3 = attack.apply(baseline_image_bytes, parameters={"std": 20.0}, seed=1000)
    assert res1.output_hash != res3.output_hash, "Different seeds must yield different outputs"

def test_image_metrics_calculation(baseline_image_bytes):
    attack = GaussianBlurAttack()
    res = attack.apply(baseline_image_bytes, parameters={"kernel_size": 7, "sigma": 2.0})
    assert res.metrics.psnr is not None
    assert res.metrics.ssim is not None
    assert res.metrics.mae is not None
    assert 0.0 <= res.metrics.ssim <= 1.0
