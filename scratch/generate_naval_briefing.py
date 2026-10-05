import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        # Top banner
        self.setFillColor(colors.HexColor("#991B1B"))
        self.rect(0, 762, 612, 30, stroke=0, fill=1)
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 9)
        self.drawCentredString(306, 773, "TOP SECRET // NOFORN // SPECIAL ACCESS REQUIRED // NAVAL COMMAND DISPATCH")

        # Bottom banner
        self.setFillColor(colors.HexColor("#991B1B"))
        self.rect(0, 0, 612, 28, stroke=0, fill=1)
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 8)
        self.drawCentredString(306, 11, f"TOP SECRET // REL TO IN // STRICT ADMISSIBILITY UNDER SECTION 63 BSA 2023 // PAGE {self._pageNumber} OF {total_pages}")
        
        # Security perimeter watermark
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.rect(26, 36, 560, 718, stroke=1, fill=0)
        self.restoreState()


def build_pdf(output_path):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=38,
        rightMargin=38,
        topMargin=50,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        alignment=1
    )
    
    sub_title_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0284C7'),
        alignment=1,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=6
    )

    meta_label = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#475569')
    )
    
    meta_val = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A')
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    )

    table_cell_mono = ParagraphStyle(
        'TableCellMono',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#0284C7')
    )

    story = []

    # Title Header Block
    story.append(Spacer(1, 4))
    story.append(Paragraph("MINISTRY OF DEFENCE | INTEGRATED DEFENCE HEADQUARTERS", sub_title_style))
    story.append(Paragraph("DIRECTORATE OF NAVAL OPERATIONS & WEAPONS SYSTEMS (WESEE)", title_style))
    story.append(Paragraph("TACTICAL MARITIME OPERATIONS & QUANTUM-SECURED DISPATCH", ParagraphStyle('SubSub', parent=sub_title_style, textColor=colors.HexColor('#DC2626'), fontSize=10, leading=13)))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0F172A"), spaceBefore=4, spaceAfter=8))

    # Metadata Block
    meta_data = [
        [
            Paragraph("<b>DISPATCH ID:</b>", meta_label), Paragraph("IN-NAV-OPS-2026-0842-ALPHA", meta_val),
            Paragraph("<b>SECURITY LEVEL:</b>", meta_label), Paragraph("<font color='#DC2626'><b>TOP SECRET // EYES ONLY</b></font>", meta_val)
        ],
        [
            Paragraph("<b>ORIGINATOR:</b>", meta_label), Paragraph("Vice Adm. R. K. Mukherjee, PVSM, AVSM", meta_val),
            Paragraph("<b>DISTRIBUTION:</b>", meta_label), Paragraph("Eastern & Western Naval Commands", meta_val)
        ],
        [
            Paragraph("<b>DATE OF ISSUE:</b>", meta_label), Paragraph("05 October 2026 - 0600Z", meta_val),
            Paragraph("<b>PROVENANCE:</b>", meta_label), Paragraph("AegisTrace Post-Quantum Enclave Active", meta_val)
        ],
        [
            Paragraph("<b>ROOT HASH:</b>", meta_label), Paragraph("9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822c", meta_val),
            Paragraph("<b>STATUTORY BASIS:</b>", meta_label), Paragraph("Bharatiya Sakshya Adhiniyam 2023 § 63", meta_val)
        ]
    ]

    t_meta = Table(meta_data, colWidths=[90, 180, 95, 170])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # Section 1: Executive Mission Directive
    story.append(Paragraph("1. OPERATIONAL SITUATION & MARITIME DOMAIN AWARENESS", h1_style))
    story.append(Paragraph(
        "1.1. In accordance with Operation Trident Surge, maritime surface groups and undersea assets deployed across "
        "the Malacca Approaches and Bay of Bengal littoral zones are transitioning to <b>Condition Aegis-1</b>. "
        "All tactical transmissions, acoustic telemetry packets, and sovereign satellite uplinks must incorporate "
        "client-side ephemeral dynamic watermarking under the SIH26237 forensic architecture.",
        body_style
    ))
    story.append(Paragraph(
        "1.2. Intercept indicators confirm hostile adversary SIGINT trawlers operating in international transit lanes. "
        "Under no circumstances shall classified operational coordinates or electronic warfare frequencies be exported "
        "without cryptographic origin attestation. Every release is unique and permanently traceable to the recipient officer.",
        body_style
    ))

    # Section 2: Fleet Key Distribution Matrix
    story.append(Paragraph("2. POST-QUANTUM LATTICE KEY MATRIX (ML-KEM-768)", h1_style))
    story.append(Paragraph(
        "The following battle group flag vessels and command liaison officers have been issued post-quantum "
        "decryption parameters conforming to NIST FIPS 203/204 standard specifications:",
        body_style
    ))

    key_table_data = [
        [
            Paragraph("FLAG VESSEL / RECIPIENT", table_header),
            Paragraph("CALL SIGN", table_header),
            Paragraph("ENCLAVE ID", table_header),
            Paragraph("POST-QUANTUM KEY FINGERPRINT", table_header),
            Paragraph("STATUS", table_header)
        ],
        [
            Paragraph("INS Vikrant (Flagship)", table_cell),
            Paragraph("TIGER-01", table_cell),
            Paragraph("ENC_VIKRANT_01", table_cell),
            Paragraph("fips203_768_a91b...34c8", table_cell_mono),
            Paragraph("<font color='#16A34A'><b>ACTIVE</b></font>", table_cell)
        ],
        [
            Paragraph("INS Kolkata (Air Warfare)", table_cell),
            Paragraph("COBRA-04", table_cell),
            Paragraph("ENC_KOLKATA_02", table_cell),
            Paragraph("fips203_768_d44e...91fa", table_cell_mono),
            Paragraph("<font color='#16A34A'><b>ACTIVE</b></font>", table_cell)
        ],
        [
            Paragraph("INS Arihant (Sub-Surface)", table_cell),
            Paragraph("SHADOW-09", table_cell),
            Paragraph("ENC_ARIHANT_03", table_cell),
            Paragraph("fips203_768_88b1...02ee", table_cell_mono),
            Paragraph("<font color='#16A34A'><b>ACTIVE</b></font>", table_cell)
        ],
        [
            Paragraph("Cmdr. Rajesh Sharma (Tactical Ops)", table_cell),
            Paragraph("EAGLE-LEAD", table_cell),
            Paragraph("ENC_SHARMA_NAV", table_cell),
            Paragraph("fips203_768_7a8b...5e6f", table_cell_mono),
            Paragraph("<font color='#0284C7'><b>ENROLLED</b></font>", table_cell)
        ],
        [
            Paragraph("Maj. Priya Nair (Cyber Defense)", table_cell),
            Paragraph("SENTINEL-02", table_cell),
            Paragraph("ENC_PRIYA_DEF", table_cell),
            Paragraph("fips203_768_3a5b...0a1b", table_cell_mono),
            Paragraph("<font color='#0284C7'><b>ENROLLED</b></font>", table_cell)
        ]
    ]

    t_keys = Table(key_table_data, colWidths=[130, 75, 95, 175, 60])
    t_keys.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#0F172A')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_keys)
    story.append(Spacer(1, 10))

    # Section 3: Forensic Attribution & Defense Invariants
    story.append(Paragraph("3. SPREAD-SPECTRUM FORENSIC INVARIANTS & ANTI-COLLUSION BOUNDS", h1_style))
    story.append(Paragraph(
        "3.1. <b>Zero Server Storage Footprint:</b> In accordance with naval air-gap security guidelines, the master "
        "document remains unified and un-duplicated. Each recipient's secure enclave injects an imperceptible "
        "pseudo-noise orthogonal carrier (Barker-13 preamble + 128-bit BCH payload) directly into spatial/DCT coordinates "
        "at the instant of decryption.",
        body_style
    ))
    story.append(Paragraph(
        "3.2. <b>Smartphone Screen-Capture Robustness:</b> The modulation maintains mathematical survivability across "
        "optical capture, severe perspective distortion (up to 45° off-axis tilt), moiré pattern frequency interference, "
        "and aggressive image re-compression (JPEG Q≥25 / WhatsApp 90% web compression).",
        body_style
    ))
    story.append(Paragraph(
        "3.3. <b>Tardos Traitor-Tracing Collusion Defense:</b> Coalition attacks by up to c=5 colluding recipients attempting "
        "linear combination, interleaving, or min/max pixel blending are provably bounded. The Dirichlet evaluation engine "
        "guarantees simultaneous detection of all conspiring parties with false alarm probability P<sub>FA</sub> < 10<sup>-6</sup>.",
        body_style
    ))

    # Section 4: Dual-Officer Judicial Attestation Protocol
    story.append(Spacer(1, 6))
    story.append(Paragraph("4. STATUTORY ADMISSIBILITY UNDER SECTION 63, BHARATIYA SAKSHYA ADHINIYAM 2023", h1_style))
    story.append(Paragraph(
        "Any forensic attribution produced from an unauthorized disclosure of this document is governed by the "
        "<b>Sabha Dual-Officer Attestation Protocol</b>. The digital certificate rendered by AegisTrace constitutes an "
        "admissible Section 63 BSA electronic record, permanently validated by an immutable RFC-6962 Merkle tree ledger.",
        body_style
    ))

    # Signatures Table
    sig_data = [
        [
            Paragraph("<b>CHIEF TECHNICAL EXAMINER:</b>", meta_label),
            Paragraph("<b>NAVAL PROVOST MARSHAL / JUDICIAL CUSTODIAN:</b>", meta_label)
        ],
        [
            Paragraph("<b>Dr. V. Raman</b>, Ph.D. (Cryptology)<br/>"
                      "Chief Forensic Scientist, Naval Cyber Command<br/>"
                      "<i>Cryptographic Affirmation: ML-DSA-65 Validated</i>", table_cell),
            Paragraph("<b>Capt. S. Sengupta</b>, IN<br/>"
                      "Naval Provost Marshal, Directorate of Naval Security<br/>"
                      "<i>Custodial Affirmation: Chain of Custody Continuous</i>", table_cell)
        ],
        [
            Paragraph("Digital Signature: <font color='#0284C7'><b>ML-DSA-65#RAMAN-842911-PASS</b></font>", table_cell_mono),
            Paragraph("Digital Signature: <font color='#0284C7'><b>ML-DSA-65#SENGUPTA-911024-SEAL</b></font>", table_cell_mono)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[267, 268])
    t_sig.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#94A3B8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    story.append(Spacer(1, 4))
    story.append(KeepTogether([t_sig]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated defense-grade classified PDF: {output_path}")

if __name__ == '__main__':
    targets = [
        r"C:\Projects\SIH26237\Naval_Operations_Briefing.pdf",
        r"C:\Projects\SIH26237\apps\web\public\Naval_Operations_Briefing.pdf",
        r"C:\Projects\SIH26237\data\demo_fixtures\Naval_Operations_Briefing.pdf"
    ]
    for target in targets:
        build_pdf(target)
