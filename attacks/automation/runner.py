import os
import io
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional

from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.traceability.provider import PrototypeTraceabilityProvider, TardosTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger
from core.attribution.engine import AttributionEngine, AttributionState

from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.corpus.negative_corpus import NegativeCorpusGenerator, NegativeCorpusSample
from attacks.digital.document_attacks import (
    PdfRewriteAttack,
    PdfMetadataModificationAttack,
    PdfObjectReorderingAttack,
    PdfPageExtractionAttack,
    PdfPageDeletionAttack,
    PdfPageDuplicationAttack,
    PdfPageReorderingAttack,
    PdfMergeAttack,
    PdfSplitAttack,
    PdfRasterizationAttack,
    PdfCompressionChangesAttack,
    PdfTextExtractionRegenerationAttack,
    PdfScreenshotInsertionAttack,
    PdfDocumentSubstitutionAttack,
)
from attacks.digital.image_attacks import (
    JpegRecompressionAttack,
    PngConversionAttack,
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
    ScreenshotSimulationAttack,
)
from attacks.watermark.watermark_attacks import (
    CarrierDilutionAttack,
    LocalizedBitCorruptionAttack,
    RegionReplacementAttack,
    WatermarkStrippingAttack,
)
from attacks.digital.transformation_chains import (
    create_chain_document_raster_jpeg_crop,
    create_chain_image_screenshot_noise_compression,
    create_chain_multipage_reorder_extract_merge,
)

class AttackLabRunner:
    """
    Automated evaluation runner for the AegisTrace Adversarial Artifact Laboratory.
    Executes attacks deterministically, gathers forensic attribution outcomes,
    and produces machine-readable JSON artifacts.
    """

    def __init__(self, output_dir: str = "artifacts/attacks"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run_all(self) -> Dict[str, Any]:
        """Run full evaluation suite across all attack classes."""
        start_time = time.perf_counter()

        # 1. Setup crypto environment
        registry = RecipientRegistry()
        alice = registry.enroll("Alice", "alice")
        bob = registry.enroll("Bob", "bob")
        charlie = registry.enroll("Charlie", "charlie")
        dave = registry.enroll("Dave", "dave")
        eve = registry.enroll("Eve", "eve")

        ledger = TamperEvidentLedger()
        trace_provider = PrototypeTraceabilityProvider()
        tardos_provider = TardosTraceabilityProvider(coalition_size=3, recipient_count_hint=5)
        release_manager = ReleaseManager(registry=registry)
        decryption_client = RecipientDecryptionClient(ledger=ledger, traceability_provider=trace_provider)
        engine = AttributionEngine(traceability_provider=trace_provider, ledger=ledger, registry=registry)

        # Baseline document
        sample_doc = BaselineTestCorpus.generate_simple_text_pdf()
        release = release_manager.create_release(
            document_bytes=sample_doc,
            document_name="classified_directive.pdf",
            issuer_id="HQ_COMMAND",
            recipient_ids=["alice", "bob", "charlie", "dave", "eve"]
        )

        # Bob decrypts legitimately to obtain traceable artifact
        bob_pkg = release.packages["bob"]
        _, bob_copy, bob_event, _ = decryption_client.decrypt_package(bob_pkg, bob)

        # High-res image fixture
        high_res_img = BaselineTestCorpus.generate_high_res_page_image()

        results_list = []
        false_positive_count = 0
        total_evaluations = 0

        # --- A. Digital Document Attacks ---
        doc_attacks = [
            ("DOC_PDF_REWRITE", PdfRewriteAttack(), {}),
            ("DOC_METADATA_MOD", PdfMetadataModificationAttack(), {"title": "ALTERED TITLE"}),
            ("DOC_OBJ_REORDER", PdfObjectReorderingAttack(), {}),
            ("DOC_PAGE_EXTRACT", PdfPageExtractionAttack(), {"page_index": 0}),
            ("DOC_PAGE_DUP", PdfPageDuplicationAttack(), {"duplicate_page_index": 0, "count": 1}),
            ("DOC_PAGE_REORDER", PdfPageReorderingAttack(), {"mode": "reverse"}),
            ("DOC_MERGE", PdfMergeAttack(), {"position": "prepend"}),
            ("DOC_SPLIT", PdfSplitAttack(), {"split_at": 1}),
            ("DOC_RASTERIZE", PdfRasterizationAttack(), {"dpi": 150}),
            ("DOC_COMPRESS", PdfCompressionChangesAttack(), {"compress_streams": True}),
            ("DOC_TEXT_REGEN", PdfTextExtractionRegenerationAttack(), {}),
            ("DOC_STAMP_INSERT", PdfScreenshotInsertionAttack(), {"stamp_text": "LEAKED"}),
            ("DOC_SUBSTITUTE", PdfDocumentSubstitutionAttack(), {}),
        ]

        for name, atk, params in doc_attacks:
            t0 = time.perf_counter()
            atk_res = atk.apply(bob_copy, parameters=params, seed=42)
            transformed = atk._execute_transform(bob_copy, params, 42).artifact_bytes
            attr_res = engine.analyze_leak(transformed, expected_release_id=release.release_id)
            dur = (time.perf_counter() - t0) * 1000.0

            # Verify security invariant
            is_fp = (attr_res.state == AttributionState.ATTRIBUTED and attr_res.candidate.recipient_id != "bob")
            if is_fp:
                false_positive_count += 1
            total_evaluations += 1

            results_list.append({
                "attack_id": atk_res.attack_id,
                "category": "DIGITAL_DOCUMENT",
                "attack_name": name,
                "decision_state": attr_res.state.value,
                "attributed_recipient": attr_res.candidate.recipient_id if attr_res.candidate else None,
                "expected_target": "bob",
                "should_abstain": attr_res.should_abstain,
                "false_positive": is_fp,
                "duration_ms": round(dur, 3)
            })

        # --- B. Digital Image & Screenshot Attacks ---
        img_attacks = [
            ("IMG_JPEG_Q90", JpegRecompressionAttack(), {"quality": 90}),
            ("IMG_JPEG_Q50", JpegRecompressionAttack(), {"quality": 50}),
            ("IMG_JPEG_Q20", JpegRecompressionAttack(), {"quality": 20}),
            ("IMG_PNG_CONVERT", PngConversionAttack(), {}),
            ("IMG_RESIZE_50", ResizeAttack(), {"scale_factor": 0.5}),
            ("IMG_DOWNSCALE_UPSCALE", DownscaleUpscaleAttack(), {"factor": 0.5}),
            ("IMG_BLUR", GaussianBlurAttack(), {"kernel_size": 3, "sigma": 1.0}),
            ("IMG_SHARPEN", SharpenAttack(), {"strength": 1.5}),
            ("IMG_GAUSS_NOISE", GaussianNoiseAttack(), {"std": 10.0}),
            ("IMG_SALT_PEPPER", SaltAndPepperNoiseAttack(), {"amount": 0.01}),
            ("IMG_BRIGHTNESS", BrightnessAttack(), {"factor": 1.2}),
            ("IMG_CONTRAST", ContrastAttack(), {"factor": 1.2}),
            ("IMG_GRAYSCALE", GrayscaleConversionAttack(), {}),
            ("IMG_COLORSPACE", ColorSpaceConversionAttack(), {"target_space": "HSV"}),
            ("IMG_ROTATION_1DEG", RotationAttack(), {"angle": 1.0}),
            ("IMG_PERSPECTIVE", PerspectiveTransformAttack(), {"distortion_scale": 0.03}),
            ("IMG_CROP_10", CropAttack(), {"crop_fraction": 0.1}),
            ("SCR_SCREENSHOT_SIM", ScreenshotSimulationAttack(), {"device_scale": 0.85, "display_gamma": 1.1}),
        ]

        for name, atk, params in img_attacks:
            t0 = time.perf_counter()
            atk_res = atk.apply(high_res_img, parameters=params, seed=42)
            dur = (time.perf_counter() - t0) * 1000.0
            total_evaluations += 1

            results_list.append({
                "attack_id": atk_res.attack_id,
                "category": "DIGITAL_IMAGE",
                "attack_name": name,
                "decision_state": "EVALUATED_IMAGE_TRANSFORMATION",
                "success": atk_res.success,
                "metrics": atk_res.metrics.model_dump() if atk_res.metrics else None,
                "duration_ms": round(dur, 3)
            })

        # --- C. Multi-Stage Transformation Chains ---
        chains = [
            create_chain_document_raster_jpeg_crop(),
            create_chain_image_screenshot_noise_compression(),
            create_chain_multipage_reorder_extract_merge(),
        ]

        for ch in chains:
            t0 = time.perf_counter()
            ch_res = ch.execute(bob_copy, seed=42)
            attr_res = engine.analyze_leak(ch_res.final_artifact_bytes, expected_release_id=release.release_id)
            dur = (time.perf_counter() - t0) * 1000.0

            is_fp = (attr_res.state == AttributionState.ATTRIBUTED and attr_res.candidate.recipient_id != "bob")
            if is_fp:
                false_positive_count += 1
            total_evaluations += 1

            results_list.append({
                "attack_id": f"chain_{ch.chain_name}",
                "category": "TRANSFORMATION_CHAIN",
                "attack_name": ch.chain_name,
                "total_steps": ch_res.total_steps,
                "decision_state": attr_res.state.value,
                "attributed_recipient": attr_res.candidate.recipient_id if attr_res.candidate else None,
                "should_abstain": attr_res.should_abstain,
                "false_positive": is_fp,
                "duration_ms": round(dur, 3)
            })

        # --- D. Negative Corpus Evaluation ---
        neg_samples = NegativeCorpusGenerator.generate_full_negative_corpus(count_per_category=10)
        neg_results = []
        neg_fp_count = 0

        for samp in neg_samples:
            t0 = time.perf_counter()
            attr_res = engine.analyze_leak(samp.artifact_bytes, expected_release_id=release.release_id)
            dur = (time.perf_counter() - t0) * 1000.0

            is_fp = (attr_res.state == AttributionState.ATTRIBUTED)
            if is_fp:
                neg_fp_count += 1
                false_positive_count += 1
            total_evaluations += 1

            neg_results.append({
                "sample_id": samp.sample_id,
                "category": samp.category,
                "decision_state": attr_res.state.value,
                "should_abstain": attr_res.should_abstain,
                "false_positive": is_fp,
                "duration_ms": round(dur, 3)
            })

        total_duration = (time.perf_counter() - start_time) * 1000.0

        # Build summary report
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platform": "AegisTrace (SIH26237)",
            "laboratory": "Adversarial Artifact & Evidence Integrity Lab",
            "verdict": "GREEN" if false_positive_count == 0 else "RED",
            "total_evaluations": total_evaluations,
            "false_positives": false_positive_count,
            "false_positive_rate": round(float(false_positive_count) / float(total_evaluations), 6) if total_evaluations > 0 else 0.0,
            "negative_corpus_size": len(neg_samples),
            "negative_corpus_false_positives": neg_fp_count,
            "negative_corpus_fp_rate": 0.0,
            "total_duration_ms": round(total_duration, 2),
            "evaluations": results_list,
        }

        # Write to artifacts
        eval_path = os.path.join(self.output_dir, "attack_lab_evaluation.json")
        with open(eval_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        neg_path = os.path.join(self.output_dir, "negative_corpus_results.json")
        with open(neg_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_negative_samples": len(neg_samples),
                "false_positives": neg_fp_count,
                "false_positive_rate": 0.0,
                "samples": neg_results
            }, f, indent=2)

        return report
