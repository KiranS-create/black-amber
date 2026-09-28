"""
AegisTrace Final Golden Case Demonstration Subsystem.
Smart India Hackathon 2026 — Project ID: SIH26237
Code Name: Black Amber

Provides canonical, deterministic, air-gapped forensic golden demonstration,
verifiable offline evidence packaging, fail-closed evidence fusion, and tamper testing.
"""

from core.demo.golden_case import (
    GoldenDemoEngine,
    GoldenRunManifest,
    GoldenStepStatus,
    generate_golden_document_canvas,
)

__all__ = [
    "GoldenDemoEngine",
    "GoldenRunManifest",
    "GoldenStepStatus",
    "generate_golden_document_canvas",
]
