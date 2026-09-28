import io
import json
import base64
import hashlib
import random
from typing import List, Dict, Any, Tuple
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw

class NegativeCorpusSample:
    """Represents a single negative corpus test sample."""
    def __init__(
        self,
        sample_id: str,
        category: str,
        artifact_bytes: bytes,
        description: str,
        expected_state: str = "ABSTAIN",  # "NO_SIGNAL", "INSUFFICIENT_EVIDENCE", "CONFLICT", "ABSTAIN"
        metadata: Dict[str, Any] = None
    ):
        self.sample_id = sample_id
        self.category = category
        self.artifact_bytes = artifact_bytes
        self.description = description
        self.expected_state = expected_state
        self.metadata = metadata or {}

class NegativeCorpusGenerator:
    """
    Constructs a diverse negative corpus (100+ deterministic samples)
    to rigorously evaluate the false-positive rate of AegisTrace.
    """

    @staticmethod
    def generate_clean_unwatermarked_pdf(index: int = 1) -> bytes:
        """Category 1: Clean unwatermarked PDF document."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(54, 730, f"CLEAN UNWATERMARKED DOCUMENT #{index}")
        c.setFont("Helvetica", 10)
        c.drawString(54, 700, "This document has never been registered, marked, or processed through AegisTrace.")
        c.drawString(54, 680, "No cryptographic markers or watermarks are present in any stream.")
        c.drawString(54, 650, f"Sample unique salt: {hashlib.sha256(f'clean_{index}'.encode()).hexdigest()[:16]}")
        c.showPage()
        c.save()
        return buf.getvalue()

    @staticmethod
    def generate_unrelated_release_pdf(index: int = 1) -> bytes:
        """Category 2: Document with a marker bound to an unrelated / foreign release ID."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(54, 730, f"FOREIGN RELEASE DOCUMENT #{index}")
        c.setFont("Helvetica", 10)
        c.drawString(54, 700, "Issued by a different external organization / unknown release ID.")
        c.showPage()
        c.save()
        raw_pdf = buf.getvalue()

        # Append marker referencing unrelated release
        marker_data = {
            "document_id": f"doc_foreign_{index:04d}",
            "release_id": f"rel_foreign_unknown_{index:04d}",
            "recipient_id": "unregistered_external_user",
            "document_hash": hashlib.sha256(raw_pdf).hexdigest(),
            "signature_token": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            "timestamp": "2025-01-01T00:00:00Z",
            "metadata": {"unrelated": True}
        }
        b64 = base64.b64encode(json.dumps(marker_data).encode()).decode()
        trailer = f"\n%% SIH26237-TRACEABILITY-MARKER-START\n%% {b64}\n%% SIH26237-TRACEABILITY-MARKER-END\n".encode()
        return raw_pdf + trailer

    @staticmethod
    def generate_unregistered_recipient_pdf(index: int = 1) -> bytes:
        """Category 3: Document referencing an unregistered recipient ID."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(54, 730, f"UNREGISTERED RECIPIENT #{index}")
        c.drawString(54, 700, "Assigned to an identity not enrolled in the PKI recipient registry.")
        c.showPage()
        c.save()
        raw_pdf = buf.getvalue()

        marker_data = {
            "document_id": "doc_unregistered_001",
            "release_id": "rel_valid_format_but_fake",
            "recipient_id": f"ghost_user_{index:04d}",
            "document_hash": hashlib.sha256(raw_pdf).hexdigest(),
            "signature_token": hashlib.sha256(f"ghost_{index}".encode()).hexdigest(),
            "timestamp": "2026-09-26T12:00:00Z"
        }
        b64 = base64.b64encode(json.dumps(marker_data).encode()).decode()
        trailer = f"\n%% SIH26237-TRACEABILITY-MARKER-START\n%% {b64}\n%% SIH26237-TRACEABILITY-MARKER-END\n".encode()
        return raw_pdf + trailer

    @staticmethod
    def generate_visually_similar_pdf(index: int = 1) -> bytes:
        """Category 4: Visually similar near-duplicate layout PDF with slightly altered text."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(54, 730, "CLASSIFIED OPERATIONAL DIRECTIVE - ALPHA (RE-DRAFT)")
        c.setFont("Helvetica", 10)
        c.drawString(54, 700, "Security Classification: TOP SECRET // SIH26237 // NOFORN")
        c.drawString(54, 680, "Issuing Authority: Central Distribution Directorate")
        c.drawString(54, 650, f"Simulated near-duplicate variant #{index} with modified internal hash.")
        c.showPage()
        c.save()
        return buf.getvalue()

    @staticmethod
    def generate_reconstructed_ocr_pdf(index: int = 1) -> bytes:
        """Category 5: OCR reconstructed plain PDF (clean typography, no hidden streams)."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont("Times-Roman", 12)
        c.drawString(72, 700, f"[RECONSTRUCTED VIA OCR SCANNER ENGINE #{index}]")
        c.drawString(72, 680, "Plain text extraction from photographic print scan.")
        c.drawString(72, 660, "All binary streams, fonts, and object structures have been re-synthesized.")
        c.showPage()
        c.save()
        return buf.getvalue()

    @staticmethod
    def generate_decoy_public_report(index: int = 1) -> bytes:
        """Category 6: Public decoy document (e.g. budget report)."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(54, 730, f"PUBLIC MUNICIPAL INFRASTRUCTURE BUDGET #{index}")
        c.setFont("Helvetica", 10)
        c.drawString(54, 700, "Open Public Record - Free Distribution Allowed.")
        c.drawString(54, 670, "Fiscal Year 2026-2027 Capital Expenditure Allocations.")
        c.showPage()
        c.save()
        return buf.getvalue()

    @staticmethod
    def generate_counterfeit_marker_pdf(index: int = 1) -> bytes:
        """Category 7: Counterfeit/forged marker with bogus HMAC token attempting to frame Bob."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.drawString(54, 700, f"COUNTERFEIT FORGERY SAMPLE #{index}")
        c.showPage()
        c.save()
        raw_pdf = buf.getvalue()

        marker_data = {
            "document_id": "doc_target_001",
            "release_id": "rel_target_001",
            "recipient_id": "bob",  # Attempting to frame Bob
            "document_hash": hashlib.sha256(raw_pdf).hexdigest(),
            "signature_token": "deadbeef" * 8,  # Forged/fake signature token
            "timestamp": "2026-09-26T12:00:00Z"
        }
        b64 = base64.b64encode(json.dumps(marker_data).encode()).decode()
        trailer = f"\n%% SIH26237-TRACEABILITY-MARKER-START\n%% {b64}\n%% SIH26237-TRACEABILITY-MARKER-END\n".encode()
        return raw_pdf + trailer

    @staticmethod
    def generate_random_marker_noise_pdf(index: int = 1) -> bytes:
        """Category 8: Random garbage bytes formatted with marker delimiters."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.drawString(54, 700, f"RANDOM NOISE ENVELOPE #{index}")
        c.showPage()
        c.save()
        raw_pdf = buf.getvalue()

        random_garbage = base64.b64encode(bytes([random.randint(0, 255) for _ in range(64)])).decode()
        trailer = f"\n%% SIH26237-TRACEABILITY-MARKER-START\n%% {random_garbage}\n%% SIH26237-TRACEABILITY-MARKER-END\n".encode()
        return raw_pdf + trailer

    @staticmethod
    def generate_truncated_corrupted_pdf(index: int = 1) -> bytes:
        """Category 9: Truncated/corrupted PDF stream."""
        clean = NegativeCorpusGenerator.generate_clean_unwatermarked_pdf(index)
        # Chop off last 40% of bytes (corrupts trailer and cross-reference table)
        return clean[:len(clean) * 3 // 5]

    @staticmethod
    def generate_unwatermarked_image(index: int = 1) -> bytes:
        """Category 10: Clean unwatermarked image (PNG)."""
        img = Image.new("RGB", (400, 400), color=(245, 245, 250))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 380, 380], outline=(100, 100, 150), width=2)
        draw.text((40, 100), f"CLEAN UNWATERMARKED IMAGE #{index}", fill=(20, 20, 50))
        draw.text((40, 140), "Standard photo / scan with zero forensic carrier.", fill=(80, 80, 80))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @classmethod
    def generate_full_negative_corpus(cls, count_per_category: int = 10) -> List[NegativeCorpusSample]:
        """
        Generate a comprehensive suite of 100+ negative samples across 10 categories.
        """
        samples: List[NegativeCorpusSample] = []

        categories = [
            ("clean_unwatermarked", cls.generate_clean_unwatermarked_pdf, "Clean unwatermarked text PDF", "NO_SIGNAL"),
            ("unrelated_release", cls.generate_unrelated_release_pdf, "Marker bound to foreign/unrelated release ID", "CONFLICT"),
            ("unregistered_recipient", cls.generate_unregistered_recipient_pdf, "Marker referencing non-existent recipient ID", "INSUFFICIENT_EVIDENCE"),
            ("visually_similar", cls.generate_visually_similar_pdf, "Visually similar near-duplicate document", "NO_SIGNAL"),
            ("reconstructed_ocr", cls.generate_reconstructed_ocr_pdf, "Reconstructed plain text OCR document", "NO_SIGNAL"),
            ("decoy_public_report", cls.generate_decoy_public_report, "Unclassified public municipal report", "NO_SIGNAL"),
            ("counterfeit_forgery", cls.generate_counterfeit_marker_pdf, "Counterfeit marker with forged HMAC token", "INSUFFICIENT_EVIDENCE"),
            ("random_marker_noise", cls.generate_random_marker_noise_pdf, "Corrupted non-JSON payload in marker delimiters", "NO_SIGNAL"),
            ("truncated_corrupted", cls.generate_truncated_corrupted_pdf, "Truncated PDF binary stream", "NO_SIGNAL"),
            ("unwatermarked_image", cls.generate_unwatermarked_image, "Clean unwatermarked PNG image", "NO_SIGNAL"),
        ]

        for cat_name, generator_fn, desc, exp_state in categories:
            for idx in range(1, count_per_category + 1):
                sample_id = f"neg_{cat_name}_{idx:03d}"
                raw_bytes = generator_fn(idx)
                samples.append(
                    NegativeCorpusSample(
                        sample_id=sample_id,
                        category=cat_name,
                        artifact_bytes=raw_bytes,
                        description=f"{desc} (Sample {idx})",
                        expected_state=exp_state,
                        metadata={"index": idx, "category": cat_name, "size_bytes": len(raw_bytes)}
                    )
                )

        return samples
