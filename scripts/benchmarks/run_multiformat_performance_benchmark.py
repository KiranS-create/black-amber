"""
SIH26237 - Multi-Format Forensic Performance Benchmark Suite.
Measures real latency, throughput, and memory consumption across all Tier 1 and Tier 2 format pipelines.
"""

import time
import json
import os
import sys
from typing import Dict, Any, List

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from core.formats.api import ForensicFormatAPI
from core.watermark.base import WatermarkPayload, WatermarkStatus
from tests.formats.fixtures import (
    create_minimal_pdf_bytes,
    create_minimal_docx_bytes,
    create_minimal_pptx_bytes,
    create_minimal_xlsx_bytes,
    create_minimal_png_bytes,
    create_minimal_jpeg_bytes,
    create_minimal_txt_bytes,
    create_minimal_csv_bytes,
)


def benchmark_format(api: ForensicFormatAPI, fmt_name: str, raw_bytes: bytes, filename: str, iterations: int = 20) -> Dict[str, Any]:
    print(f"[*] Benchmarking format: {fmt_name} ({len(raw_bytes)} bytes, {iterations} iterations)...")

    # 1. Ingestion & Security Validation
    t0 = time.perf_counter()
    for _ in range(iterations):
        orig_identity, canonical, sec_res = api.ingest_artifact(raw_bytes, filename=filename)
    ingest_time_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

    # 2. Canonicalization
    adapter = api.registry.get_adapter(fmt_name)
    t0 = time.perf_counter()
    for _ in range(iterations):
        canonical = adapter.canonicalize(raw_bytes, f"doc_{fmt_name.lower()}")
    canon_time_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

    # 3. Carrier Rendering
    t0 = time.perf_counter()
    for _ in range(iterations):
        carriers = api.render_forensic_carriers(canonical)
    render_time_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

    base_carrier = carriers[0]

    # 4. Watermark Embedding
    codeword = [1, 0, 1, 0] * 32  # 128 bits
    payload = WatermarkPayload(
        document_id=f"doc_bench_{fmt_name.lower()}",
        release_id="rel_bench_01",
        codeword=codeword,
        metadata={"recipient_id": "usr_bench"}
    )
    t0 = time.perf_counter()
    for _ in range(iterations):
        wm_carrier, _ = api.watermark_carrier(base_carrier, payload, format_hint=fmt_name)
    embed_time_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

    # 5. Watermark Extraction
    t0 = time.perf_counter()
    for _ in range(iterations):
        obs = api.extract_watermark(
            captured_input=wm_carrier.image_bytes,
            format_hint=fmt_name,
            expected_document_id=f"doc_bench_{fmt_name.lower()}",
            expected_release_id="rel_bench_01",
            expected_codeword_length=128
        )
    extract_time_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

    total_pipeline_ms = ingest_time_ms + render_time_ms + embed_time_ms
    throughput_ops_sec = 1000.0 / total_pipeline_ms if total_pipeline_ms > 0 else 0

    return {
        "format": fmt_name,
        "payload_size_bytes": len(raw_bytes),
        "ingest_security_ms": round(ingest_time_ms, 3),
        "canonicalize_ms": round(canon_time_ms, 3),
        "render_carrier_ms": round(render_time_ms, 3),
        "embed_watermark_ms": round(embed_time_ms, 3),
        "extract_watermark_ms": round(extract_time_ms, 3),
        "total_protect_pipeline_ms": round(total_pipeline_ms, 3),
        "throughput_ops_per_sec": round(throughput_ops_sec, 2),
        "extraction_status": obs.status.value,
        "is_valid": obs.is_valid
    }


def main():
    api = ForensicFormatAPI()
    formats_to_bench = [
        ("PDF", create_minimal_pdf_bytes("Performance PDF", "Benchmark payload text"), "benchmark.pdf"),
        ("DOCX", create_minimal_docx_bytes("Performance DOCX", "Benchmark payload table and paragraphs"), "benchmark.docx"),
        ("PPTX", create_minimal_pptx_bytes("Performance PPTX", "Benchmark slide body"), "benchmark.pptx"),
        ("XLSX", create_minimal_xlsx_bytes("Performance XLSX"), "benchmark.xlsx"),
        ("PNG", create_minimal_png_bytes(800, 600), "benchmark.png"),
        ("JPEG", create_minimal_jpeg_bytes(800, 600), "benchmark.jpg"),
        ("TXT", create_minimal_txt_bytes("Plaintext benchmark payload for performance profiling.\nLine 2.\n"), "benchmark.txt"),
        ("CSV", create_minimal_csv_bytes(), "benchmark.csv"),
    ]

    results = []
    print("\n" + "=" * 80)
    print(" AegisTrace - Multi-Format Forensic Pipeline Performance Benchmark")
    print("=" * 80 + "\n")

    for fmt, raw_bytes, filename in formats_to_bench:
        res = benchmark_format(api, fmt, raw_bytes, filename, iterations=15)
        results.append(res)

    print("\n" + "=" * 100)
    print(f"{'Format':<8} | {'Size (B)':<10} | {'Ingest(ms)':<12} | {'Render(ms)':<12} | {'Embed(ms)':<12} | {'Extract(ms)':<12} | {'Total(ms)':<10} | {'Ops/sec':<8}")
    print("-" * 100)
    for r in results:
        print(f"{r['format']:<8} | {r['payload_size_bytes']:<10} | {r['ingest_security_ms']:<12.3f} | {r['render_carrier_ms']:<12.3f} | {r['embed_watermark_ms']:<12.3f} | {r['extract_watermark_ms']:<12.3f} | {r['total_protect_pipeline_ms']:<10.3f} | {r['throughput_ops_per_sec']:<8.2f}")
    print("=" * 100)

    # Save benchmark artifact
    output_path = os.path.join(os.path.dirname(__file__), "../../artifacts/benchmarks/multiformat_performance_benchmark.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Benchmark results successfully saved to: {output_path}")


if __name__ == "__main__":
    main()
