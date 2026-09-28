"""
SIH26237 - Multi-Format Test Fixtures and Synthetic Document Generators.
Generates valid in-memory bytes for PDF, DOCX, PPTX, XLSX, PNG, JPEG, TXT, CSV, RTF, and ODF.
"""

import io
import cv2
import zipfile
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET


def create_minimal_pdf_bytes(title: str = "Test PDF Document", content: str = "AegisTrace PDF Content") -> bytes:
    """Creates a valid, well-formed minimal PDF document in memory."""
    from pypdf import PdfWriter
    # Create simple PDF via reportlab or minimal canvas if available, or direct pypdf stream
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595.0, 842.0))
    c.drawString(100, 750, title)
    c.drawString(100, 700, content)
    c.showPage()
    c.save()
    return buf.getvalue()


def create_minimal_docx_bytes(title: str = "Test DOCX Document", content: str = "AegisTrace DOCX Content") -> bytes:
    """Creates a valid OpenXML DOCX archive in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # [Content_Types].xml
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            '</Types>'
        )
        zf.writestr("[Content_Types].xml", content_types)

        # _rels/.rels
        rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '</Relationships>'
        )
        zf.writestr("_rels/.rels", rels)

        # docProps/core.xml
        core_props = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            f'<dc:title>{title}</dc:title>'
            '<dc:creator>AegisTrace Security</dc:creator>'
            '</cp:coreProperties>'
        )
        zf.writestr("docProps/core.xml", core_props)

        # word/document.xml
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>'
            '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>' + title + '</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>' + content + '</w:t></w:r></w:p>'
            '<w:tbl>'
            '<w:tr><w:tc><w:p><w:r><w:t>Header1</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Header2</w:t></w:r></w:p></w:tc></w:tr>'
            '<w:tr><w:tc><w:p><w:r><w:t>Val1</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Val2</w:t></w:r></w:p></w:tc></w:tr>'
            '</w:tbl>'
            '</w:body>'
            '</w:document>'
        )
        zf.writestr("word/document.xml", doc_xml)

    return buf.getvalue()


def create_minimal_pptx_bytes(title: str = "Test PPTX Slide", content: str = "AegisTrace Slide Bullet") -> bytes:
    """Creates a valid OpenXML PPTX presentation in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            '<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            '</Types>'
        )
        zf.writestr("[Content_Types].xml", content_types)

        rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
            '</Relationships>'
        )
        zf.writestr("_rels/.rels", rels)

        pres_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:sldIdLst><p:sldId id="256" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></p:sldIdLst>'
            '</p:presentation>'
        )
        zf.writestr("ppt/presentation.xml", pres_xml)

        slide_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<p:cSld><p:spTree>'
            '<p:sp><p:txBody><a:p><a:r><a:t>' + title + '</a:t></a:r></a:p></p:txBody></p:sp>'
            '<p:sp><p:txBody><a:p><a:r><a:t>' + content + '</a:t></a:r></a:p></p:txBody></p:sp>'
            '</p:spTree></p:cSld>'
            '</p:sld>'
        )
        zf.writestr("ppt/slides/slide1.xml", slide_xml)

    return buf.getvalue()


def create_minimal_xlsx_bytes(title: str = "Test Spreadsheet") -> bytes:
    """Creates a valid OpenXML XLSX workbook in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
            '</Types>'
        )
        zf.writestr("[Content_Types].xml", content_types)

        rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        )
        zf.writestr("_rels/.rels", rels)

        wb_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheets><sheet name="Financials" sheetId="1" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></sheets>'
            '</workbook>'
        )
        zf.writestr("xl/workbook.xml", wb_xml)

        sst_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="3" uniqueCount="3">'
            '<si><t>Department</t></si>'
            '<si><t>Budget</t></si>'
            '<si><t>Engineering</t></si>'
            '</sst>'
        )
        zf.writestr("xl/sharedStrings.xml", sst_xml)

        sheet_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData>'
            '<row r="1">'
            '<c r="A1" t="s"><v>0</v></c>'
            '<c r="B1" t="s"><v>1</v></c>'
            '</row>'
            '<row r="2">'
            '<c r="A2" t="s"><v>2</v></c>'
            '<c r="B2"><v>500000</v></c>'
            '</row>'
            '</sheetData>'
            '</worksheet>'
        )
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)

    return buf.getvalue()


def create_minimal_png_bytes(width: int = 400, height: int = 300) -> bytes:
    """Creates a valid PNG image in memory."""
    img = np.full((height, width, 3), 230, dtype=np.uint8)
    cv2.putText(img, "AegisTrace PNG", (50, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    _, buf = cv2.imencode(".png", img)
    return bytes(buf)


def create_minimal_jpeg_bytes(width: int = 400, height: int = 300) -> bytes:
    """Creates a valid JPEG image in memory."""
    img = np.full((height, width, 3), 230, dtype=np.uint8)
    cv2.putText(img, "AegisTrace JPEG", (50, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    _, buf = cv2.imencode(".jpg", img)
    return bytes(buf)


def create_minimal_txt_bytes(text: str = "AegisTrace Security Plaintext Document\nConfidential Data Line 2") -> bytes:
    """Creates plaintext UTF-8 bytes."""
    return text.encode("utf-8")


def create_minimal_csv_bytes() -> bytes:
    """Creates valid CSV bytes."""
    return "ID,Name,Department,Clearance\nusr_01,Alice,Security,TopSecret\nusr_02,Bob,Forensics,Secret\n".encode("utf-8")


def create_minimal_rtf_bytes() -> bytes:
    """Creates valid RTF document bytes."""
    return b"{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Courier;}}\\f0\\fs24 AegisTrace RTF Document Content\\par Line 2}"


def create_minimal_odt_bytes() -> bytes:
    """Creates valid OpenDocument Text (.odt) archive in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        content_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
            '<office:body><office:text>'
            '<text:p>AegisTrace ODT Paragraph Content</text:p>'
            '</office:text></office:body>'
            '</office:document-content>'
        )
        zf.writestr("content.xml", content_xml)
    return buf.getvalue()
