import os
import glob
import pytest
from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.digital.image_attacks import (
    JpegRecompressionAttack,
    ResizeAttack,
    CropAttack,
    PerspectiveTransformAttack,
)
from attacks.digital.document_attacks import (
    PdfRewriteAttack,
    PdfRasterizationAttack,
)
from attacks.measurement.evaluator import RobustnessEvaluator, BenchmarkTiming

@pytest.fixture
def evaluator(tmp_path):
    return RobustnessEvaluator(artifacts_dir=str(tmp_path))

def test_jpeg_quality_parameter_sweep(evaluator):
    img_bytes = BaselineTestCorpus.generate_high_res_page_image()
    attack = JpegRecompressionAttack()
    quality_levels = [95, 80, 50, 30, 10]

    entries = evaluator.run_parameter_sweep(
        attack=attack,
        input_bytes=img_bytes,
        param_name="quality",
        param_values=quality_levels,
        seed=42
    )

    assert len(entries) == 5
    for i, entry in enumerate(entries):
        assert entry.parameter_value == quality_levels[i]
        assert entry.attack_result.success is True
        assert entry.attack_result.parameters["quality"] == quality_levels[i]

    # Verify JSON files were saved
    saved_files = glob.glob(os.path.join(evaluator.artifacts_dir, "*.json"))
    assert len(saved_files) == 5

def test_timing_benchmarks_on_representative_attacks(evaluator):
    img_bytes = BaselineTestCorpus.generate_high_res_page_image()
    pdf_bytes = BaselineTestCorpus.generate_simple_text_pdf()

    representative_attacks = [
        (JpegRecompressionAttack(), img_bytes, {"quality": 75}),
        (ResizeAttack(), img_bytes, {"scale_factor": 0.5}),
        (CropAttack(), img_bytes, {"crop_fraction": 0.1}),
        (PerspectiveTransformAttack(), img_bytes, {"distortion_scale": 0.05}),
        (PdfRewriteAttack(), pdf_bytes, {}),
        (PdfRasterizationAttack(), pdf_bytes, {"dpi": 100}),
    ]

    for attack, target_bytes, params in representative_attacks:
        timing = evaluator.benchmark_attack(
            attack=attack,
            input_bytes=target_bytes,
            parameters=params,
            iterations=3,
            seed=42
        )
        assert isinstance(timing, BenchmarkTiming)
        assert timing.samples == 3
        assert timing.mean_ms > 0
        assert timing.median_ms > 0
        assert timing.p95_ms >= timing.median_ms
        assert timing.input_size_bytes == len(target_bytes)
        assert timing.output_size_bytes > 0
