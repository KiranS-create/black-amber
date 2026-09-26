"""
SIH26237 - End-to-End Print-Camera Watermark Pipeline
Combines Geometric Synchronization (OpenCV ArUco), Reed-Solomon ECC (reedsolo),
and Direct Sequence Spread Spectrum (DSSS) modulation into unified WatermarkEncoder
and WatermarkDecoder implementations.
"""

from typing import Tuple, List, Optional, Dict, Any, Union
import numpy as np
import cv2
from PIL import Image
import io

from core.watermark.base import (
    WatermarkEncoder,
    WatermarkDecoder,
    WatermarkPayload,
    WatermarkObservation,
    WatermarkStatus,
)
import struct
from core.watermark.sync import GeometricSynchronizer, CanonicalCanvasSpec
from core.watermark.ecc import WatermarkPayloadCodec, DEFAULT_RS_PARITY_BYTES, PREAMBLE_MAGIC, bytes_to_bits
from core.watermark.carrier import CarrierModulator, CarrierConfig, CarrierStrategy



def ensure_cv2_image(carrier_input: Union[bytes, np.ndarray, Image.Image]) -> np.ndarray:
    """Converts bytes, PIL image, or array into a standard BGR OpenCV numpy array."""
    if isinstance(carrier_input, np.ndarray):
        if len(carrier_input.shape) == 2:
            return cv2.cvtColor(carrier_input, cv2.COLOR_GRAY2BGR)
        return carrier_input.copy()
    elif isinstance(carrier_input, bytes):
        # Decode from bytes (JPEG, PNG, etc.)
        nparr = np.frombuffer(carrier_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            return img
        # If PDF or unparseable, render a clean blank page canvas
        img = np.ones((1000, 800, 3), dtype=np.uint8) * 255
        cv2.putText(img, "[DOCUMENT PAGE CARRIER]", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 50, 50), 2)
        return img
    elif isinstance(carrier_input, Image.Image):
        return cv2.cvtColor(np.array(carrier_input), cv2.COLOR_RGB2BGR)
    else:
        raise ValueError(f"Unsupported image input type: {type(carrier_input)}")


class PrintCameraWatermarkEncoder(WatermarkEncoder):
    """
    Encodes recipient-specific fingerprint payloads into a document page canvas
    equipped with geometric synchronization fiducials, Reed-Solomon ECC, and DSSS modulation.
    """

    def __init__(
        self,
        canvas_spec: Optional[CanonicalCanvasSpec] = None,
        carrier_config: Optional[CarrierConfig] = None,
        rs_parity_bytes: int = DEFAULT_RS_PARITY_BYTES
    ):
        self.canvas_spec = canvas_spec or CanonicalCanvasSpec()
        self.carrier_config = carrier_config or CarrierConfig()
        self.synchronizer = GeometricSynchronizer(self.canvas_spec)
        self.codec = WatermarkPayloadCodec(rs_parity_bytes)
        self.modulator = CarrierModulator(self.carrier_config)

    def encode(
        self,
        carrier_input: Union[bytes, np.ndarray, Image.Image],
        payload: WatermarkPayload,
        as_bytes: bool = False,
        format: str = "PNG",
        **kwargs
    ) -> Union[np.ndarray, bytes]:
        """
        Embeds the payload into the document canvas.
        Returns BGR numpy array or encoded image bytes (PNG/JPEG).
        """
        img = ensure_cv2_image(carrier_input)

        # 1. Resize/pad canvas to canonical dimensions if not matching
        target_w, target_h = self.canvas_spec.width, self.canvas_spec.height
        if (img.shape[1], img.shape[0]) != (target_w, target_h):
            img = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_AREA)

        # 2. Embed 4-corner synchronization fiducials
        anchored_canvas = self.synchronizer.embed_fiducial_anchors(img)

        # 3. Assemble and ECC-encode payload bitstream
        encoded_bits = self.codec.encode_payload(
            document_id=payload.document_id,
            release_id=payload.release_id,
            codeword=payload.codeword
        )

        # 4. Modulate payload bitstream using DSSS onto the canvas
        watermarked_canvas, mod_telemetry = self.modulator.modulate(anchored_canvas, encoded_bits)

        if as_bytes:
            ext = f".{format.lower()}"
            success, encoded_buf = cv2.imencode(ext, watermarked_canvas)
            if not success:
                raise RuntimeError(f"Failed to encode image to format {format}")
            return bytes(encoded_buf)

        return watermarked_canvas


class PrintCameraWatermarkDecoder(WatermarkDecoder):
    """
    Decodes fingerprint observations from smartphone camera captures or digital images.
    Implements fail-closed abstention: returns NO_SIGNAL on missing/damaged markers
    and INVALID on document-binding/CRC mismatches.
    """

    def __init__(
        self,
        canvas_spec: Optional[CanonicalCanvasSpec] = None,
        carrier_config: Optional[CarrierConfig] = None,
        rs_parity_bytes: int = DEFAULT_RS_PARITY_BYTES
    ):
        self.canvas_spec = canvas_spec or CanonicalCanvasSpec()
        self.carrier_config = carrier_config or CarrierConfig()
        self.synchronizer = GeometricSynchronizer(self.canvas_spec)
        self.codec = WatermarkPayloadCodec(rs_parity_bytes)
        self.modulator = CarrierModulator(self.carrier_config)

    def decode(
        self,
        captured_input: Union[bytes, np.ndarray, Image.Image],
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        expected_codeword_length: Optional[int] = None,
        codeword_length_hint: Optional[int] = None,
        **kwargs
    ) -> WatermarkObservation:
        """
        Executes full physical recovery pipeline:
        1. Geometric perspective rectification via OpenCV ArUco homography
        2. DSSS matched-filter demodulation
        3. Reed-Solomon error correction, length verification, and CRC32 verification
        4. Structured fail-closed observation generation with granular timing telemetry
        """
        import time

        t_total_start = time.perf_counter()
        img = ensure_cv2_image(captured_input)
        img_res = f"{img.shape[1]}x{img.shape[0]}"

        # 1. Geometric Synchronization & Perspective Rectification
        t_sync_start = time.perf_counter()
        sync_ok, rectified_canvas, sync_telemetry = self.synchronizer.detect_and_rectify(img)
        t_sync_end = time.perf_counter()
        sync_latency_ms = round((t_sync_end - t_sync_start) * 1000.0, 2)

        if not sync_ok or rectified_canvas is None:
            t_total_end = time.perf_counter()
            return WatermarkObservation(
                status=WatermarkStatus.NO_SIGNAL,
                is_valid=False,
                confidence=0.0,
                synchronization_success=False,
                telemetry={
                    "stage": "synchronization",
                    "sync_telemetry": sync_telemetry,
                    "image_resolution": img_res,
                    "sync_latency_ms": sync_latency_ms,
                    "total_decode_latency_ms": round((t_total_end - t_total_start) * 1000.0, 2)
                }
            )

        # 2. Capacity & Dimensions Verification
        m = expected_codeword_length or codeword_length_hint or 128
        total_bytes = 2 + 4 + 2 + ((m + 7) // 8) + 4 + self.codec.rs_parity_bytes
        total_encoded_bits = total_bytes * 8

        # Calculate available slots in canonical canvas ROI
        left, top, right, bottom = self.modulator._get_embedding_bounds()
        bs = self.carrier_config.block_size
        grid_cols = (right - left) // bs
        grid_rows = (bottom - top) // bs
        total_slots = grid_cols * grid_rows

        if total_slots < total_encoded_bits:
            t_total_end = time.perf_counter()
            return WatermarkObservation(
                status=WatermarkStatus.INVALID,
                is_valid=False,
                confidence=0.0,
                symbol_count=0,
                synchronization_success=True,
                homography_error=sync_telemetry.get("reprojection_error", 0.0),
                telemetry={
                    "stage": "demodulation",
                    "reason": "capacity_exceeded",
                    "error": f"Required {total_encoded_bits} bits > available {total_slots} slots in strategy {self.carrier_config.strategy.value}",
                    "image_resolution": img_res,
                    "sync_latency_ms": sync_latency_ms,
                    "total_decode_latency_ms": round((t_total_end - t_total_start) * 1000.0, 2)
                }
            )

        # 3. DSSS Matched-Filter Demodulation
        t_demod_start = time.perf_counter()
        preamble_bits = bytes_to_bits(struct.pack(">H", PREAMBLE_MAGIC))
        raw_bits, soft_confidences, demod_telemetry = self.modulator.demodulate(
            rectified_canvas, total_encoded_bits, preamble_bits=preamble_bits
        )
        t_demod_end = time.perf_counter()
        demod_latency_ms = round((t_demod_end - t_demod_start) * 1000.0, 2)

        # 4. Reed-Solomon Error Correction & CRC Validation
        t_ecc_start = time.perf_counter()
        ecc_ok, recovered_codeword, ecc_telemetry = self.codec.decode_payload(
            raw_bits=raw_bits,
            expected_document_id=expected_document_id,
            expected_release_id=expected_release_id,
            expected_codeword_length=expected_codeword_length
        )
        t_ecc_end = time.perf_counter()
        ecc_latency_ms = round((t_ecc_end - t_ecc_start) * 1000.0, 2)
        t_total_end = time.perf_counter()
        total_latency_ms = round((t_total_end - t_total_start) * 1000.0, 2)

        combined_telemetry = {
            "sync": sync_telemetry,
            "demod": demod_telemetry,
            "ecc": ecc_telemetry,
            "image_resolution": img_res,
            "reprojection_error": sync_telemetry.get("reprojection_error", 0.0),
            "sync_latency_ms": sync_latency_ms,
            "demod_latency_ms": demod_latency_ms,
            "ecc_latency_ms": ecc_latency_ms,
            "total_decode_latency_ms": total_latency_ms
        }

        # 5. Observation Status Decision
        if not ecc_ok or recovered_codeword is None:
            # If error is due to document-binding or length mismatch, status is INVALID
            err_msg = ecc_telemetry.get("error", "")
            if "binding mismatch" in err_msg or "length mismatch" in err_msg:
                return WatermarkObservation(
                    status=WatermarkStatus.INVALID,
                    is_valid=False,
                    confidence=0.0,
                    symbol_count=0,
                    synchronization_success=True,
                    homography_error=sync_telemetry.get("reprojection_error", 0.0),
                    telemetry=combined_telemetry
                )
            
            # Uncorrectable ECC errors -> Partial observation
            # Extract raw soft symbols for Tardos soft scoring
            return WatermarkObservation(
                status=WatermarkStatus.PARTIAL,
                is_valid=False,
                confidence=0.25,
                symbol_count=0,
                observed_symbols=[],
                soft_confidences=soft_confidences[:m],
                synchronization_success=True,
                homography_error=sync_telemetry.get("reprojection_error", 0.0),
                telemetry=combined_telemetry
            )

        # Successfully recovered and verified!
        # Confidence derived from reprojection error and errata count
        errata = ecc_telemetry.get("errata_count", 0)
        max_errata = self.codec.rs_parity_bytes // 2
        ecc_margin = 1.0 - (errata / max(max_errata, 1)) * 0.4
        reproj_factor = max(0.0, 1.0 - sync_telemetry.get("reprojection_error", 0.0) * 0.1)
        final_confidence = round(float(np.clip(ecc_margin * reproj_factor, 0.5, 0.99)), 4)

        return WatermarkObservation(
            status=WatermarkStatus.RECOVERED,
            is_valid=True,
            confidence=final_confidence,
            raw_ber=round(errata / float(total_bytes), 4),
            symbol_count=len(recovered_codeword),
            document_release_id=f"{expected_document_id}:{expected_release_id}" if expected_document_id else None,
            observed_symbols=recovered_codeword,
            soft_confidences=soft_confidences[:len(recovered_codeword)],
            synchronization_success=True,
            homography_error=sync_telemetry.get("reprojection_error", 0.0),
            telemetry=combined_telemetry
        )
