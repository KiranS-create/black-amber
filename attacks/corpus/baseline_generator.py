import io
import hashlib
from typing import Dict, Tuple, Optional
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from core.traceability.provider import PrototypeTraceabilityProvider, TraceabilityMarker

class BaselineTestCorpus:
    """
    Generates a deterministic test corpus for the attack laboratory:
      1. Simple text document (PDF)
      2. Multi-page document (PDF)
      3. Image-containing document (PDF)
      4. High-resolution document page (PNG)
      5. Synthetic watermark/fingerprint carrier fixture (PDF with prototype marker)
    """

    @staticmethod
    def generate_simple_text_pdf() -> bytes:
        """1. Simple text PDF."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(54, 730, "CLASSIFIED OPERATIONAL DIRECTIVE - ALPHA")
        c.setFont("Helvetica", 10)
        c.drawString(54, 700, "Security Classification: TOP SECRET // SIH26237 // NOFORN")
        c.drawString(54, 680, "Issuing Authority: Central Distribution Directorate")
        c.drawString(54, 650, "1.0 Purpose and Operational Scope:")
        c.drawString(54, 630, "This document establishes the protocols for post-quantum key encapsulation")
        c.drawString(54, 615, "and immutable provenance verification across distributed operational nodes.")
        c.drawString(54, 585, "2.0 Dissemination Controls:")
        c.drawString(54, 565, "Strict non-disclosure agreements apply to all authorized recipients.")
        c.drawString(54, 550, "Cryptographic markers are authenticated via HMAC-SHA256 tokens.")
        c.showPage()
        c.save()
        return buf.getvalue()

    @staticmethod
    def generate_multipage_pdf() -> bytes:
        """2. Multi-page PDF (3 pages)."""
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        
        pages_content = [
            ("EXECUTIVE SUMMARY - SECTION I", [
                "This report outlines the structural resilience of multi-recipient releases.",
                "Authorized keyholders are registered with individual ML-KEM-768 keypairs.",
                "Each decryption event is immutably anchored to the ledger."
            ]),
            ("TECHNICAL ARCHITECTURE - SECTION II", [
                "Post-quantum signatures (ML-DSA-65) prevent non-repudiation vulnerabilities.",
                "Ledger entries form a SHA-256 hash chain verified from root to tip.",
                "Adversarial tampering immediately triggers fail-closed abstention."
            ]),
            ("SECURITY EVALUATION - SECTION III", [
                "Extensive adversarial testing covers digital image, PDF, and print-cam attacks.",
                "The system rejects forged markers with 100% precision.",
                "Final sign-off authorized by Chief Security Testing Engineer."
            ])
        ]

        for idx, (title, lines) in enumerate(pages_content):
            c.setFont("Helvetica-Bold", 14)
            c.drawString(54, 730, f"{title} (Page {idx+1} of 3)")
            c.setFont("Helvetica", 10)
            y = 690
            for line in lines:
                c.drawString(54, y, line)
                y -= 25
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(54, 50, f"SIH26237 Confidential Multi-Page Baseline Document — Page {idx+1}")
            c.showPage()

        c.save()
        return buf.getvalue()

    @staticmethod
    def generate_image_containing_pdf() -> bytes:
        """3. Image-containing PDF."""
        # Create a synthetic 200x200 badge/seal image
        seal_img = Image.new("RGB", (200, 200), color=(240, 240, 245))
        draw = ImageDraw.Draw(seal_img)
        draw.rectangle([10, 10, 190, 190], outline=(20, 40, 120), width=4)
        draw.ellipse([30, 30, 170, 170], outline=(180, 20, 20), width=2)
        draw.text((50, 90), "OFFICIAL SEAL", fill=(20, 20, 20))
        draw.text((55, 110), "SIH26237", fill=(120, 20, 20))

        img_buf = io.BytesIO()
        seal_img.save(img_buf, format="PNG")
        img_buf.seek(0)

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(54, 730, "VERIFIED CREDENTIAL BRIEFING")
        c.setFont("Helvetica", 10)
        c.drawString(54, 700, "Includes embedded official seal and image XObjects for attack testing.")
        
        # Embed image
        c.drawImage(ImageReader(img_buf), 54, 480, width=150, height=150)
        
        c.drawString(54, 450, "Verification metadata embedded below image.")
        c.showPage()
        c.save()
        return buf.getvalue()

    @staticmethod
    def generate_high_res_page_image() -> bytes:
        """4. High-resolution raster page image (1200 x 1600 PNG)."""
        img = Image.new("RGB", (1200, 1600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Draw borders and title
        draw.rectangle([50, 50, 1150, 1550], outline=(0, 0, 0), width=3)
        draw.rectangle([60, 60, 1140, 1540], outline=(100, 100, 100), width=1)

        draw.text((100, 120), "HIGH RESOLUTION DIGITAL TEST CARRIER", fill=(0, 0, 0))
        draw.text((100, 170), "Resolution: 1200 x 1600 px | Subsampling: 4:4:4", fill=(50, 50, 50))

        # Synthetic pattern grid for frequency analysis
        for x in range(100, 1100, 100):
            draw.line([(x, 250), (x, 1450)], fill=(220, 220, 220), width=1)
        for y in range(250, 1450, 100):
            draw.line([(100, y), (1100, y)], fill=(220, 220, 220), width=1)

        draw.text((100, 280), "Lorem ipsum dolor sit amet, consectetur adipiscing elit.", fill=(0, 0, 0))
        draw.text((100, 310), "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.", fill=(0, 0, 0))
        draw.text((100, 340), "Cryptographic carrier fixture prepared for adversarial stress tests.", fill=(0, 0, 0))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def generate_synthetic_carrier_fixture(
        recipient_id: str = "bob",
        document_id: str = "doc_baseline_001",
        release_id: str = "rel_baseline_001"
    ) -> Tuple[bytes, TraceabilityMarker]:
        """
        5. Synthetic watermark/fingerprint carrier fixture.
        Embeds a genuine PrototypeTraceabilityMarker into the simple text PDF using the public provider.
        """
        raw_pdf = BaselineTestCorpus.generate_simple_text_pdf()
        raw_hash = hashlib.sha256(raw_pdf).hexdigest()

        provider = PrototypeTraceabilityProvider()
        marker = provider.issue_marker(
            document_id=document_id,
            release_id=release_id,
            recipient_id=recipient_id,
            document_hash=raw_hash,
            metadata={"test_fixture": True}
        )
        marked_pdf = provider.embed_marker(raw_pdf, marker)
        return (marked_pdf, marker)
