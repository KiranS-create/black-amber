#!/usr/bin/env python3
"""
SIH26237 — Official SIH 2026 PowerPoint Generator
==================================================

Builds `presentation/SIH26237_Final.pptx` by taking the official SIH 2026 template
`SIH2026-IDEA-Presentation-Format.pptx` and populating all 6 slides with precise,
rigorous, and verified SIH26237 content while preserving 100% of the template's
visual identity, geometry, aspect ratio (16:9), footer bar, and official SIH branding.
"""

import os
import shutil
import sys
from pathlib import Path
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_PATH = Path(r"C:\Users\kiran akash\Downloads\SIH2026-IDEA-Presentation-Format.pptx")
OUTPUT_PATH = PROJECT_ROOT / "presentation" / "SIH26237_Final.pptx"

# Colors
COLOR_DARK_BLUE = RGBColor(16, 44, 87)
COLOR_TEXT_DARK = RGBColor(33, 37, 41)
COLOR_MUTED = RGBColor(108, 117, 125)
COLOR_ACCENT_BLUE = RGBColor(13, 110, 253)

def create_presentation():
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found at {TEMPLATE_PATH}")

    # Ensure output dir exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Open presentation from template
    prs = Presentation(str(TEMPLATE_PATH))
    print(f"Loaded template with {len(prs.slides)} slides. Dimensions: {prs.slide_width} x {prs.slide_height}")

    # Verify 16:9
    ratio = prs.slide_width / prs.slide_height
    print(f"Aspect ratio: {ratio:.3f} (16:9 is ~1.778)")

    # -------------------------------------------------------------
    # SLIDE 1: TITLE PAGE
    # -------------------------------------------------------------
    slide1 = prs.slides[0]
    for shape in slide1.shapes:
        if shape.name == "TextBox 9" and shape.has_text_frame:
            tf = shape.text_frame
            tf.clear()
            tf.word_wrap = True
            
            items = [
                ("Problem Statement ID \u2013 ", "SIH26237"),
                ("Problem Statement Title \u2013 ", "Post-Quantum Document Leak Attribution"),
                ("Theme \u2013 ", "Security & Surveillance / Cybersecurity"),
                ("PS Category \u2013 ", "Software"),
                ("Team ID \u2013 ", "[Team ID]"),
                ("Team Name \u2013 ", "Ad Astra (iTantra)"),
            ]
            
            for idx, (label, val) in enumerate(items):
                p = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
                p.space_after = Pt(8)
                
                r1 = p.add_run()
                r1.text = label
                r1.font.name = "Arial"
                r1.font.size = Pt(20)
                r1.font.bold = True
                r1.font.color.rgb = COLOR_TEXT_DARK
                
                r2 = p.add_run()
                r2.text = val
                r2.font.name = "Arial"
                r2.font.size = Pt(20)
                r2.font.bold = (idx in [0, 1, 5])
                r2.font.color.rgb = COLOR_DARK_BLUE if (idx in [0, 1, 5]) else COLOR_TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 2: PROPOSED SOLUTION
    # -------------------------------------------------------------
    slide2 = prs.slides[1]
    # Update Team Name Oval
    for shape in slide2.shapes:
        if "Oval" in shape.name and shape.has_text_frame:
            shape.text_frame.text = "Ad Astra"
            shape.text_frame.paragraphs[0].font.size = Pt(11)
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        elif shape.name == "Title 1" and shape.has_text_frame:
            shape.text_frame.text = "PROPOSED SOLUTION"
            shape.text_frame.paragraphs[0].font.name = "Times New Roman"
            shape.text_frame.paragraphs[0].font.size = Pt(32)
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        elif shape.name == "TextBox 8" and shape.has_text_frame:
            # Main content
            shape.left = Inches(0.8)
            shape.top = Inches(1.5)
            shape.width = Inches(11.7)
            shape.height = Inches(5.2)
            
            tf = shape.text_frame
            tf.clear()
            tf.word_wrap = True
            
            # Workflow Chain Callout
            p0 = tf.paragraphs[0]
            p0.space_after = Pt(10)
            r = p0.add_run()
            r.text = "CORE PIPELINE:  Original Document  \u2192  ML-KEM-768 Release  \u2192  Sovereign Decrypt  \u2192  Tardos Fingerprint  \u2192  Optical Watermark  \u2192  Analog Leak  \u2192  Signal Recovery  \u2192  Evidence Fusion"
            r.font.name = "Arial"
            r.font.size = Pt(12)
            r.font.bold = True
            r.font.color.rgb = COLOR_DARK_BLUE
            
            bullets = [
                ("The Physical Leakage Boundary Problem:", " Conventional DRM & encryption protect files in transit and at rest, but fail completely once an authorized recipient renders the plaintext or prints it on paper, enabling anonymous smartphone photography leaks."),
                ("Post-Quantum Multi-Recipient Envelope:", " The authority encapsulates an ephemeral symmetric key (K_doc : AES-256-GCM) independently per recipient using NIST ML-KEM-768 (FIPS 203). Client decapsulation produces a non-repudiable ML-DSA-65 signed provenance ticket on a tamper-evident hash chain."),
                ("Collusion-Resistant Optical Carrier:", " Embeds dynamic capacity-planned Symmetric Tardos codes (c=3, \u03b51=10\u207b\u2074) through DSSS spatial modulation and Reed-Solomon ECC, synchronized via 4-corner ArUco fiducials surviving print-scan and camera perspective tilt (\u00b130\u00b0)."),
                ("Fail-Closed Evidence Fusion Engine:", " Correlates physical watermark, Tardos likelihoods, and signed provenance in an Evidence Dependency Graph. Strictly enforces Transitive Lineage Bounding to eliminate double-counting, requiring separation (\u0394 \u2265 2.5) before attributing."),
                ("Core Value Axiom:", " 'Protect the document before release, trace the recipient-specific copy after leakage, and abstain when evidence is insufficient or contradictory.'"),
            ]
            
            for heading, body in bullets:
                p = tf.add_paragraph()
                p.space_after = Pt(8)
                p.level = 0
                
                r_head = p.add_run()
                r_head.text = "\u2022  " + heading
                r_head.font.name = "Arial"
                r_head.font.size = Pt(14)
                r_head.font.bold = True
                r_head.font.color.rgb = COLOR_DARK_BLUE if "Axiom" in heading else COLOR_TEXT_DARK
                
                r_body = p.add_run()
                r_body.text = body
                r_body.font.name = "Arial"
                r_body.font.size = Pt(13.5)
                r_body.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 3: TECHNICAL APPROACH
    # -------------------------------------------------------------
    slide3 = prs.slides[2]
    for shape in slide3.shapes:
        if "Oval" in shape.name and shape.has_text_frame:
            shape.text_frame.text = "Ad Astra"
            shape.text_frame.paragraphs[0].font.size = Pt(11)
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        elif shape.name == "Title 1" and shape.has_text_frame:
            shape.text_frame.text = "TECHNICAL APPROACH"
            shape.text_frame.paragraphs[0].font.name = "Times New Roman"
            shape.text_frame.paragraphs[0].font.size = Pt(32)
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        elif shape.name == "TextBox 8" and shape.has_text_frame:
            shape.left = Inches(0.8)
            shape.top = Inches(1.5)
            shape.width = Inches(11.7)
            shape.height = Inches(5.2)
            
            tf = shape.text_frame
            tf.clear()
            tf.word_wrap = True
            
            sections = [
                ("1. Cryptographic Trust Layer (NIST FIPS 203 / 204):", [
                    ("ML-KEM-768 Key Encapsulation: ", "Wraps 256-bit ephemeral document key per recipient (11.61 ms encap). Sovereign client-side private key isolation ensures zero server key escrow."),
                    ("ML-DSA-65 Digital Signatures: ", "Sovereign client signs decryption provenance event (20.97 ms verify), committed to an immutable SHA-256 Merkle hash-chained ledger.")
                ]),
                ("2. Traceability & Optical Carrier Modulation:", [
                    ("Symmetric Tardos Traitor-Tracing: ", "Capacity planner sizes code length m = 100 \u00b7 c\u00b2 \u00b7 ln(1/\u03b51). Symbol-symmetric accumulator calculates continuous likelihoods under collusion."),
                    ("DSSS & Geometric Synchronization: ", "Spreads bitstream across spatial luminance blocks with Reed-Solomon ECC. 4 ArUco corner fiducials enable homography perspective rectification (cv2.warpPerspective).")
                ]),
                ("3. Forensic Evidence Fusion & Decision Protocol:", [
                    ("Evidence Dependency Graph: ", "Transitive derivation bounding max_{n\u2208Tree}(\u03c1n \u00b7 LLRn) eliminates double-counting between raw watermarks and derived Tardos scores."),
                    ("Fail-Closed 5-State Engine: ", "Outputs ATTRIBUTED, NO_SIGNAL, INSUFFICIENT_EVIDENCE, CONFLICT, or REVIEW_REQUIRED. Enforces candidate separation margin \u0394 = S(1) - S(2) \u2265 2.5.")
                ])
            ]
            
            for sec_idx, (sec_title, points) in enumerate(sections):
                p_sec = tf.paragraphs[0] if sec_idx == 0 else tf.add_paragraph()
                p_sec.space_after = Pt(3)
                p_sec.space_before = Pt(4) if sec_idx > 0 else Pt(0)
                
                r_sec = p_sec.add_run()
                r_sec.text = sec_title
                r_sec.font.name = "Arial"
                r_sec.font.size = Pt(14)
                r_sec.font.bold = True
                r_sec.font.color.rgb = COLOR_DARK_BLUE
                
                for p_label, p_desc in points:
                    p_sub = tf.add_paragraph()
                    p_sub.space_after = Pt(3)
                    p_sub.level = 1
                    
                    r_lbl = p_sub.add_run()
                    r_lbl.text = " \u2022  " + p_label
                    r_lbl.font.name = "Arial"
                    r_lbl.font.size = Pt(13)
                    r_lbl.font.bold = True
                    r_lbl.font.color.rgb = COLOR_TEXT_DARK
                    
                    r_dsc = p_sub.add_run()
                    r_dsc.text = p_desc
                    r_dsc.font.name = "Arial"
                    r_dsc.font.size = Pt(13)
                    r_dsc.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 4: FEASIBILITY AND VIABILITY
    # -------------------------------------------------------------
    slide4 = prs.slides[3]
    for shape in slide4.shapes:
        if "Oval" in shape.name and shape.has_text_frame:
            shape.text_frame.text = "Ad Astra"
            shape.text_frame.paragraphs[0].font.size = Pt(11)
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        elif shape.name == "Title 1" and shape.has_text_frame:
            shape.text_frame.text = "FEASIBILITY AND VIABILITY"
            shape.text_frame.paragraphs[0].font.name = "Times New Roman"
            shape.text_frame.paragraphs[0].font.size = Pt(32)
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        elif shape.name == "TextBox 8" and shape.has_text_frame:
            shape.left = Inches(0.8)
            shape.top = Inches(1.5)
            shape.width = Inches(11.7)
            shape.height = Inches(5.2)
            
            tf = shape.text_frame
            tf.clear()
            tf.word_wrap = True
            
            items = [
                ("100% Offline Air-Gapped Feasibility:", " Fully self-contained local architecture requiring zero cloud SaaS APIs or external daemons. Operates across local FastAPI REST server, SQLite metadata control plane, local filesystem artifact storage, and React/Vite web dashboard."),
                ("Sub-Second Turnkey Deployment:", " Measured clean environment reset in 349.11 ms; deterministic demo fixture generation in 140.49 ms; system health check in 209.19 ms. Starts instantly on standard Windows/Linux laptops with single command start_demo.ps1."),
                ("Adversarial Robustness & Attack Lab:", " Systematic attack evaluation across JPEG recompression (Q=10..95), downsampling (25%..75%), rotation (0.5\u00b0..5.0\u00b0), cropping (10%..30%), and simulated print-camera capture with optical blur and ambient noise."),
                ("Zero-Trust Risk Mitigation (Fail-Closed):", " Under severe destructive attacks (>30% crop or carrier wipe), Attack-Aware Reliability module dynamically attenuates confidence and strictly transitions to INSUFFICIENT_EVIDENCE, mathematically eliminating false accusations against innocent recipients."),
                ("Scientific Boundary Disclosure:", " Automated test suite evaluates 75 simulated optical capture runs (PrintCameraSimulationAttack); real physical print/scan laboratory validation is structured via standalone hardware ingestion protocol (ingest_physical_capture.py)."),
            ]
            
            for idx, (head, body) in enumerate(items):
                p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
                p.space_after = Pt(7)
                
                r_h = p.add_run()
                r_h.text = "\u2022  " + head
                r_h.font.name = "Arial"
                r_h.font.size = Pt(13.5)
                r_h.font.bold = True
                r_h.font.color.rgb = COLOR_DARK_BLUE
                
                r_b = p.add_run()
                r_b.text = body
                r_b.font.name = "Arial"
                r_b.font.size = Pt(13)
                r_b.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 5: IMPACT AND BENEFITS
    # -------------------------------------------------------------
    slide5 = prs.slides[4]
    for shape in slide5.shapes:
        if "Oval" in shape.name and shape.has_text_frame:
            shape.text_frame.text = "Ad Astra"
            shape.text_frame.paragraphs[0].font.size = Pt(11)
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        elif shape.name == "Title 1" and shape.has_text_frame:
            shape.text_frame.text = "IMPACT AND BENEFITS"
            shape.text_frame.paragraphs[0].font.name = "Times New Roman"
            shape.text_frame.paragraphs[0].font.size = Pt(32)
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        elif shape.name == "TextBox 8" and shape.has_text_frame:
            shape.left = Inches(0.8)
            shape.top = Inches(1.5)
            shape.width = Inches(11.7)
            shape.height = Inches(5.2)
            
            tf = shape.text_frame
            tf.clear()
            tf.word_wrap = True
            
            p0 = tf.paragraphs[0]
            p0.space_after = Pt(8)
            r0 = p0.add_run()
            r0.text = "OPERATIONAL IMPACT & MEASURED BENCHMARKS (SIH26237 REPOSITORY TELEMETRY)"
            r0.font.name = "Arial"
            r0.font.size = Pt(14)
            r0.font.bold = True
            r0.font.color.rgb = COLOR_DARK_BLUE
            
            metrics = [
                ("NIST Post-Quantum Cryptography Latency:", " ML-KEM-768 Encapsulation: 11.61 ms | Decapsulation: 12.40 ms | ML-DSA-65 Signature: 124.33 ms | Signature Verify: 20.97 ms | AES-256-GCM Envelope: 0.30 ms (scripts/benchmark_crypto.py)."),
                ("Optical Watermark Recovery (Simulated Channel):", " Average ArUco Sync Latency: 26.50 ms | DSSS Demodulation: 36.31 ms | Total Decode: 62.81 ms. Evaluated across 75 simulated optical capture runs with 0.0% post-ECC BER on recovered carriers."),
                ("Zero False Accusations on Negative Corpus:", " 0 false accusations observed across 50 unwatermarked / negative document evaluation runs (0.0% empirical false accusation rate; 50/50 clean fail-closed abstentions)."),
                ("Evidence Fusion Synthetic Evaluation:", " 74.0% (74/100) decision-match rate on 100-scenario held-out evaluation split under extreme compound adversarial attack corruptions. Zero false accusations against innocent enrolled recipients."),
                ("Full Regression Suite Validation:", " 43 / 43 automated unit, integration, deployment, and presentation tests passing (pytest in 6.05s). Clean Windows AMD64 portability verified."),
                ("National Defense & Enterprise Benefits:", " Closes the post-decryption 'analog hole' for defense intelligence, confidential R&D, and judicial records with legally auditable, non-repudiable provenance."),
            ]
            
            for head, body in metrics:
                p = tf.add_paragraph()
                p.space_after = Pt(6)
                
                r_h = p.add_run()
                r_h.text = "\u2022  " + head
                r_h.font.name = "Arial"
                r_h.font.size = Pt(13)
                r_h.font.bold = True
                r_h.font.color.rgb = COLOR_TEXT_DARK
                
                r_b = p.add_run()
                r_b.text = body
                r_b.font.name = "Arial"
                r_b.font.size = Pt(12.5)
                r_b.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 6: RESEARCH AND REFERENCES
    # -------------------------------------------------------------
    slide6 = prs.slides[5]
    for shape in slide6.shapes:
        if "Oval" in shape.name and shape.has_text_frame:
            shape.text_frame.text = "Ad Astra"
            shape.text_frame.paragraphs[0].font.size = Pt(11)
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        elif shape.name == "Title 1" and shape.has_text_frame:
            shape.text_frame.text = "RESEARCH AND REFERENCES"
            shape.text_frame.paragraphs[0].font.name = "Times New Roman"
            shape.text_frame.paragraphs[0].font.size = Pt(32)
            shape.text_frame.paragraphs[0].font.bold = True
            shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        elif shape.name == "TextBox 8" and shape.has_text_frame:
            shape.left = Inches(0.8)
            shape.top = Inches(1.5)
            shape.width = Inches(11.7)
            shape.height = Inches(5.2)
            
            tf = shape.text_frame
            tf.clear()
            tf.word_wrap = True
            
            sections = [
                ("Foundational Research & Standards Reused:", [
                    ("NIST FIPS 203 & FIPS 204: ", "Module-Lattice-Based Key-Encapsulation (ML-KEM) and Digital Signature Standard (ML-DSA), National Institute of Standards and Technology (2024)."),
                    ("Symmetric Tardos Codes: ", "G. Tardos, 'Optimal probabilistic fingerprint codes', ACM STOC (2003); B. Skoric et al., 'Symmetric Tardos fingerprinting codes', IEEE Trans. Inf. Theory (2008)."),
                    ("Open-Source Primitives: ", "OpenCV ArUco fiducials & perspective homography, Reed-Solomon codec, PyCryptodome AES-GCM, ReportLab, NumPy, SciPy, FastAPI.")
                ]),
                ("SIH26237 System-Level Contributions:", [
                    ("Unified Release-to-Leak Architecture: ", "Seamless pipeline from post-quantum envelope encryption to physical carrier recovery and Merkle-linked provenance logging."),
                    ("Anti-Double-Counting Lineage Traversal: ", "Evidence Dependency Graph enforcing max_{n\u2208Tree}(\u03c1n \u00b7 LLRn) bounds across derived forensic channels with \u0394 \u2265 2.5 candidate separation.")
                ]),
                ("Honest Engineering Boundaries & Closing Axiom:", [
                    ("Current Operational Boundaries: ", "Automated benchmarks evaluate simulated optical models; physical hardware validation protocol ready (ingest_physical_capture.py)."),
                    ("Core Forensic Commitment: ", "'Designed to attribute when evidence is mathematically overwhelming \u2014 and fail-closed with complete integrity when it is not.'")
                ])
            ]
            
            for sec_idx, (sec_title, points) in enumerate(sections):
                p_sec = tf.paragraphs[0] if sec_idx == 0 else tf.add_paragraph()
                p_sec.space_after = Pt(2)
                p_sec.space_before = Pt(4) if sec_idx > 0 else Pt(0)
                
                r_sec = p_sec.add_run()
                r_sec.text = sec_title
                r_sec.font.name = "Arial"
                r_sec.font.size = Pt(13.5)
                r_sec.font.bold = True
                r_sec.font.color.rgb = COLOR_DARK_BLUE
                
                for p_label, p_desc in points:
                    p_sub = tf.add_paragraph()
                    p_sub.space_after = Pt(2)
                    p_sub.level = 1
                    
                    r_lbl = p_sub.add_run()
                    r_lbl.text = " \u2022  " + p_label
                    r_lbl.font.name = "Arial"
                    r_lbl.font.size = Pt(12.5)
                    r_lbl.font.bold = True
                    r_lbl.font.color.rgb = COLOR_TEXT_DARK
                    
                    r_dsc = p_sub.add_run()
                    r_dsc.text = p_desc
                    r_dsc.font.name = "Arial"
                    r_dsc.font.size = Pt(12.5)
                    r_dsc.font.color.rgb = COLOR_TEXT_DARK

    # -------------------------------------------------------------
    # SLIDE 7: INSTRUCTION SLIDE DELETION (Preserve exactly 6 slides)
    # -------------------------------------------------------------
    if len(prs.slides) > 6:
        print(f"Removing instruction slide 7 (total was {len(prs.slides)})...")
        rId = prs.slides._sldIdLst[6].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[6]

    print(f"Final presentation has exactly {len(prs.slides)} slides.")
    prs.save(str(OUTPUT_PATH))
    print(f"[+] Successfully saved final PPTX to: {OUTPUT_PATH}")

if __name__ == "__main__":
    create_presentation()
