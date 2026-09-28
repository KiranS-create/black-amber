"""
Test Suite: Zero Production Leakage & Database Immutability Invariant.
Smart India Hackathon 2026 — Project ID: SIH26237
Code Name: Black Amber
"""

import hashlib
import pytest
from pathlib import Path
from core.demo.golden_case import GoldenDemoEngine


def test_no_production_database_leakage(tmp_path):
    """
    Assert that executing the golden demo pipeline does NOT modify or write
    any rows to production SQLite databases or stores.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    prod_db = repo_root / "data" / "metadata.sqlite3"
    artifacts_db = repo_root / "data" / "artifacts" / "artifacts_metadata.sqlite3"

    import sqlite3
    doc_count_before = 0
    leak_count_before = 0
    if prod_db.exists():
        conn = sqlite3.connect(str(prod_db))
        cur = conn.cursor()
        doc_count_before = cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        leak_count_before = cur.execute("SELECT COUNT(*) FROM leaks").fetchone()[0]
        conn.close()

    # Run golden case in isolated test path
    engine = GoldenDemoEngine(demo_dir=tmp_path / "golden_run_leakage_test")
    res = engine.run_judge(quick=True, output_json=True)
    assert res["status"] == "PASS"

    if prod_db.exists():
        conn = sqlite3.connect(str(prod_db))
        cur = conn.cursor()
        doc_count_after = cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        leak_count_after = cur.execute("SELECT COUNT(*) FROM leaks").fetchone()[0]
        demo_doc_matches = cur.execute(
            "SELECT COUNT(*) FROM documents WHERE document_id = ? OR tenant_id = ?",
            (engine.doc_id, engine.tenant_id)
        ).fetchone()[0]
        demo_leak_matches = cur.execute(
            "SELECT COUNT(*) FROM leaks WHERE suspected_document_id = ? OR tenant_id = ?",
            (engine.doc_id, engine.tenant_id)
        ).fetchone()[0]
        conn.close()

        # Zero rows added to production tables
        assert doc_count_before == doc_count_after, f"Production documents table grew by {doc_count_after - doc_count_before}"
        assert leak_count_before == leak_count_after, f"Production leaks table grew by {leak_count_after - leak_count_before}"
        assert demo_doc_matches == 0, f"Demo document leaked into production database: {demo_doc_matches} rows found"
        assert demo_leak_matches == 0, f"Demo leak leaked into production database: {demo_leak_matches} rows found"

    engine.reset()
