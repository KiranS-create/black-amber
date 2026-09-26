import io
import os
import random
from typing import Optional, Dict, Any, List
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

from attacks.base import (
    BaseAttack,
    AttackFamily,
    ExecutionMode,
    ArtifactType,
    AttackOutput,
    DegradationMetrics,
)

def create_decoy_pdf(title: str = "DECOY COVER DOCUMENT", pages: int = 1) -> bytes:
    """Helper to generate a lightweight decoy PDF document using reportlab."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for p in range(pages):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, 720, f"{title} (Page {p+1})")
        c.setFont("Helvetica", 10)
        c.drawString(72, 690, "Unclassified public release material.")
        c.drawString(72, 670, "This document serves as an unclassified decoy or carrier.")
        c.showPage()
    c.save()
    return buf.getvalue()


# 1. PDF Metadata Removal Attack
class PdfMetadataRemovalAttack(BaseAttack):
    ATTACK_NAME = "pdf_metadata_removal"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        # Clear metadata by not copying Info/Metadata or overwriting with empty dict
        writer.add_metadata({})
        
        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 2. PDF Metadata Modification Attack
class PdfMetadataModificationAttack(BaseAttack):
    ATTACK_NAME = "pdf_metadata_modification"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"
    DEFAULT_PARAMETERS = {
        "title": "FORGED TITLE - PUBLIC DOMAIN",
        "author": "Anonymous Adversary",
        "subject": "Declassified Leak",
        "keywords": "leak, declassified, altered",
    }

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        
        metadata = {
            "/Title": str(parameters.get("title", "FORGED TITLE")),
            "/Author": str(parameters.get("author", "Anonymous")),
            "/Subject": str(parameters.get("subject", "Declassified")),
            "/Keywords": str(parameters.get("keywords", "leak")),
            "/Creator": "Adversarial Lab Toolkit",
            "/Producer": "Modified PDF Engine",
        }
        writer.add_metadata(metadata)
        
        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 3. PDF Rewrite Attack
class PdfRewriteAttack(BaseAttack):
    ATTACK_NAME = "pdf_rewrite"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        # Clone metadata
        if reader.metadata:
            writer.add_metadata(reader.metadata)
        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 4. PDF Object Reordering Attack
class PdfObjectReorderingAttack(BaseAttack):
    ATTACK_NAME = "pdf_object_reordering"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        writer = PdfWriter()
        
        # Add pages in reverse order and then re-order, re-indexing indirect objects
        n = len(reader.pages)
        if n > 1:
            indices = list(range(n))
            rng = random.Random(seed if seed is not None else 42)
            rng.shuffle(indices)
            for idx in indices:
                writer.add_page(reader.pages[idx])
        else:
            # For 1-page PDF, add dummy annotation or stream to shuffle object indices
            writer.add_page(reader.pages[0])
            writer.add_metadata({"/CustomKey": "reordered_objects"})

        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 5. PDF Page Extraction Attack
class PdfPageExtractionAttack(BaseAttack):
    ATTACK_NAME = "pdf_page_extraction"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"
    DEFAULT_PARAMETERS = {"page_index": 0}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        target_idx = int(parameters.get("page_index", 0))
        if target_idx >= len(reader.pages):
            target_idx = len(reader.pages) - 1

        writer = PdfWriter()
        writer.add_page(reader.pages[target_idx])
        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 6. PDF Page Deletion Attack
class PdfPageDeletionAttack(BaseAttack):
    ATTACK_NAME = "pdf_page_deletion"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"
    DEFAULT_PARAMETERS = {"delete_page_index": 0}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        del_idx = int(parameters.get("delete_page_index", 0))
        writer = PdfWriter()

        if len(reader.pages) <= 1:
            # Cannot delete the only page in PDF; replace with minimal placeholder
            return AttackOutput(artifact_bytes=create_decoy_pdf("BLANK RESIDUAL PAGE", 1), artifact_type=ArtifactType.DOCUMENT_PDF)

        for i, page in enumerate(reader.pages):
            if i != del_idx:
                writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 7. PDF Page Duplication Attack
class PdfPageDuplicationAttack(BaseAttack):
    ATTACK_NAME = "pdf_page_duplication"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"
    DEFAULT_PARAMETERS = {"duplicate_page_index": 0, "count": 1}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        dup_idx = int(parameters.get("duplicate_page_index", 0))
        count = int(parameters.get("count", 1))
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            writer.add_page(page)
            if i == dup_idx:
                for _ in range(count):
                    writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 8. PDF Page Reordering Attack
class PdfPageReorderingAttack(BaseAttack):
    ATTACK_NAME = "pdf_page_reordering"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"
    DEFAULT_PARAMETERS = {"mode": "reverse"}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        mode = str(parameters.get("mode", "reverse")).lower()
        writer = PdfWriter()

        pages = list(reader.pages)
        if mode == "reverse":
            pages = list(reversed(pages))
        elif mode == "shuffle":
            rng = random.Random(seed if seed is not None else 42)
            rng.shuffle(pages)

        for p in pages:
            writer.add_page(p)

        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 9. PDF Merge Attack
class PdfMergeAttack(BaseAttack):
    ATTACK_NAME = "pdf_merge"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"
    DEFAULT_PARAMETERS = {"position": "append"}  # "prepend" or "append"

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        pos = str(parameters.get("position", "append")).lower()
        decoy = create_decoy_pdf("UNCLASSIFIED COVER HEADER", 1)

        reader_orig = PdfReader(io.BytesIO(artifact_bytes))
        reader_decoy = PdfReader(io.BytesIO(decoy))

        writer = PdfWriter()
        if pos == "prepend":
            for p in reader_decoy.pages:
                writer.add_page(p)
            for p in reader_orig.pages:
                writer.add_page(p)
        else:
            for p in reader_orig.pages:
                writer.add_page(p)
            for p in reader_decoy.pages:
                writer.add_page(p)

        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 10. PDF Split Attack
class PdfSplitAttack(BaseAttack):
    ATTACK_NAME = "pdf_split"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"
    DEFAULT_PARAMETERS = {"split_at": 1}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        split_at = int(parameters.get("split_at", 1))

        writer = PdfWriter()
        # Keep first partition
        limit = min(split_at, len(reader.pages))
        for i in range(limit):
            writer.add_page(reader.pages[i])

        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 11. PDF Rasterization Attack
class PdfRasterizationAttack(BaseAttack):
    ATTACK_NAME = "pdf_rasterization"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "ReportLab+Pillow"
    TOOL_VERSION = "5.0.1"
    DEFAULT_PARAMETERS = {"dpi": 150}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        # Extract text and synthesize a rasterized representation of the document
        reader = PdfReader(io.BytesIO(artifact_bytes))
        extracted_text = ""
        for p in reader.pages:
            extracted_text += (p.extract_text() or "") + "\n"

        # Create bitmap using Pillow
        width_px = 612
        height_px = 792
        img = Image.new("RGB", (width_px, height_px), color=(255, 255, 255))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        lines = extracted_text.splitlines()[:35]
        y = 40
        draw.text((40, 20), "[RASTERIZED PDF SCAN - SIMULATED BITMAP]", fill=(120, 120, 120))
        for line in lines:
            draw.text((40, y), line[:80], fill=(0, 0, 0))
            y += 20

        img_buf = io.BytesIO()
        img.save(img_buf, format="PNG")
        img_buf.seek(0)

        # Wrap into new PDF
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        from reportlab.lib.utils import ImageReader
        c.drawImage(ImageReader(img_buf), 0, 0, width=letter[0], height=letter[1])
        c.showPage()
        c.save()

        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 12. PDF Image Replacement Attack
class PdfImageReplacementAttack(BaseAttack):
    ATTACK_NAME = "pdf_image_replacement"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        writer = PdfWriter()
        
        # Create a tiny replacement 1x1 blank image
        blank_img = Image.new("RGB", (16, 16), color=(200, 200, 200))
        img_buf = io.BytesIO()
        blank_img.save(img_buf, format="PNG")
        blank_bytes = img_buf.getvalue()

        for page in reader.pages:
            # If page contains images, attempt replacement via pypdf
            try:
                for img_file in page.images:
                    page.replace_image(img_file.name, blank_img)
            except Exception:
                pass
            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 13. Print-to-PDF Simulation Attack
class PrintToPdfSimulationAttack(BaseAttack):
    ATTACK_NAME = "print_to_pdf_simulation"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"
    DEFAULT_PARAMETERS = {"virtual_driver": "Microsoft Print to PDF"}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        driver = str(parameters.get("virtual_driver", "Microsoft Print to PDF"))
        reader = PdfReader(io.BytesIO(artifact_bytes))
        writer = PdfWriter()

        for page in reader.pages:
            # Flatten form fields / annotations
            if "/Annots" in page:
                del page["/Annots"]
            writer.add_page(page)

        # Standard virtual print driver replaces Producer/Creator metadata
        writer.add_metadata({
            "/Producer": driver,
            "/Creator": "Print-to-PDF Spooler Service",
            "/Title": "Document Printout",
        })

        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 14. PDF Compression Changes Attack
class PdfCompressionChangesAttack(BaseAttack):
    ATTACK_NAME = "pdf_compression_changes"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf"
    TOOL_VERSION = "6.19.0"
    DEFAULT_PARAMETERS = {"compress_streams": True}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        compress = bool(parameters.get("compress_streams", True))
        reader = PdfReader(io.BytesIO(artifact_bytes))
        writer = PdfWriter()

        for page in reader.pages:
            p = writer.add_page(page)
            if compress:
                p.compress_content_streams()

        if compress:
            writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)

        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 15. PDF Text Extraction and Re-generation Attack
class PdfTextExtractionRegenerationAttack(BaseAttack):
    """
    Highly destructive attack: Extracts textual content from the input PDF
    and generates a completely new PDF from scratch using ReportLab.
    Strips ALL underlying binary structures, metadata, trailers, and markers.
    """
    ATTACK_NAME = "pdf_text_extraction_regeneration"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "pypdf+ReportLab"
    TOOL_VERSION = "6.19.0"

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        reader = PdfReader(io.BytesIO(artifact_bytes))
        text_lines = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            text_lines.extend(txt.splitlines())

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(54, 750, "RE-TYPESET DOCUMENT (CLEANSED ARTIFACT)")
        c.setFont("Helvetica", 10)

        y = 710
        for line in text_lines:
            c.drawString(54, y, line[:90])
            y -= 15
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 740

        c.showPage()
        c.save()
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 16. PDF Screenshot Insertion Attack
class PdfScreenshotInsertionAttack(BaseAttack):
    ATTACK_NAME = "pdf_screenshot_insertion"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "ReportLab+pypdf"
    TOOL_VERSION = "6.19.0"
    DEFAULT_PARAMETERS = {"stamp_text": "LEAKED COPY - CONFIDENTIAL"}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        stamp_text = str(parameters.get("stamp_text", "LEAKED COPY"))
        
        # Create stamp overlay PDF
        stamp_buf = io.BytesIO()
        c = canvas.Canvas(stamp_buf, pagesize=letter)
        c.setFont("Helvetica-Bold", 36)
        c.setFillColorRGB(0.9, 0.2, 0.2, alpha=0.3)
        c.saveState()
        c.translate(300, 400)
        c.rotate(45)
        c.drawCentredString(0, 0, stamp_text)
        c.restoreState()
        c.showPage()
        c.save()
        stamp_buf.seek(0)

        stamp_reader = PdfReader(stamp_buf)
        stamp_page = stamp_reader.pages[0]

        reader = PdfReader(io.BytesIO(artifact_bytes))
        writer = PdfWriter()

        for page in reader.pages:
            page.merge_page(stamp_page)
            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return AttackOutput(artifact_bytes=buf.getvalue(), artifact_type=ArtifactType.DOCUMENT_PDF)


# 17. PDF Document Substitution Attack
class PdfDocumentSubstitutionAttack(BaseAttack):
    ATTACK_NAME = "pdf_document_substitution"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT
    TOOL = "ReportLab"
    TOOL_VERSION = "5.0.1"
    DEFAULT_PARAMETERS = {"decoy_title": "UNRELATED PUBLIC BUDGET REPORT"}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        title = str(parameters.get("decoy_title", "UNRELATED PUBLIC BUDGET REPORT"))
        decoy_bytes = create_decoy_pdf(title=title, pages=2)
        return AttackOutput(artifact_bytes=decoy_bytes, artifact_type=ArtifactType.DOCUMENT_PDF)
