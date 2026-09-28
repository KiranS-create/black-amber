# SIH26237 — Official SIH 2026 Presentation Package

This directory contains the official presentation deliverables for **SIH26237** built upon the official Smart India Hackathon 2026 PowerPoint template.

---

## 1. Deliverables Summary

| File | Format | Description | Target Audience |
| :--- | :--- | :--- | :--- |
| [`SIH26237_Final.pptx`](file:///C:/Projects/SIH26237/presentation/SIH26237_Final.pptx) | PPTX | **Official 6-Slide Submission Deck** (Strictly preserves official SIH 2026 template) | SIH Evaluation Portal & Screening Panel |
| [`TEMPLATE_QA.md`](file:///C:/Projects/SIH26237/presentation/TEMPLATE_QA.md) | Markdown | 10-point template integrity and compliance QA report | Team & Lead Reviewers |
| [`slides.md`](file:///C:/Projects/SIH26237/presentation/slides.md) | Markdown | Extended 11-slide deep technical narrative deck | Technical Defense Panel |
| [`index.html`](file:///C:/Projects/SIH26237/presentation/index.html) | HTML | Standalone interactive offline web presentation | Local Laptop Presenter |
| [`SPEAKER_NOTES.md`](file:///C:/Projects/SIH26237/presentation/SPEAKER_NOTES.md) | Markdown | Slide-by-slide speaker delivery notes and timing cues | Presenter & Backup Speaker |
| [`architecture_diagram.mermaid`](file:///C:/Projects/SIH26237/presentation/architecture_diagram.mermaid) | Mermaid | Complete system architecture diagram | Architecture Reviewers |

---

## 2. PPTX Template Source & Regeneration

- **Source Template File:** Official SIH Template (`SIH2026-IDEA-Presentation-Format.pptx`)
- **Output File:** `presentation/SIH26237_Final.pptx`
- **Slide Count:** Exactly **6 Slides** (Conforms to SIH maximum 6-slide rule; instruction slide 7 safely removed)
- **Aspect Ratio:** **16:9 Widescreen** (Width: 12,192,000 / Height: 6,858,000 EMUs)

### Regeneration Command:
```powershell
python scripts/demo/generate_sih_pptx.py
```

### Validation Command:
```powershell
pytest tests/presentation/test_template_integrity.py -v
```

---

## 3. Live Demo Integration

The presentation explains the architecture, while the working system provides proof:

- **Live Web UI:** `http://127.0.0.1:5173` (Launch with `.\deployment\start_demo.ps1`)
- **Interactive Python CLI:** `python scripts/demo/run_live_demo.py`
- **Headless Rapid Validator:** `python scripts/demo/run_quick_demo.py`
- **Live Demo Script:** [`artifacts/presentation/DEMO_SCRIPT.md`](file:///C:/Projects/SIH26237/artifacts/presentation/DEMO_SCRIPT.md)
- **Presenter Checklist:** [`artifacts/presentation/PRESENTER_CHECKLIST.md`](file:///C:/Projects/SIH26237/artifacts/presentation/PRESENTER_CHECKLIST.md)
- **Judge Q&A:** [`artifacts/presentation/JUDGE_QA.md`](file:///C:/Projects/SIH26237/artifacts/presentation/JUDGE_QA.md)
