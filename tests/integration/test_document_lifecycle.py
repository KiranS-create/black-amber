import hashlib
import io
import pytest
from fastapi.testclient import TestClient

def test_document_upload_pdf(client: TestClient, sample_pdf_bytes: bytes):
    expected_hash = hashlib.sha256(sample_pdf_bytes).hexdigest()
    
    response = client.post(
        "/documents",
        files={"file": ("test_doc.pdf", sample_pdf_bytes, "application/pdf")},
        data={"document_name": "Test Master PDF"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["document_name"] == "Test Master PDF"
    assert data["original_document_hash"] == expected_hash
    assert data["size_bytes"] == len(sample_pdf_bytes)
    assert data["mime_type"] == "application/pdf"
    assert data["document_id"].startswith("doc_")

    doc_id = data["document_id"]

    # Retrieve metadata
    get_res = client.get(f"/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["original_document_hash"] == expected_hash

    # Download document bytes
    down_res = client.get(f"/documents/{doc_id}/download")
    assert down_res.status_code == 200
    assert down_res.content == sample_pdf_bytes

def test_document_upload_png(client: TestClient, sample_png_bytes: bytes):
    expected_hash = hashlib.sha256(sample_png_bytes).hexdigest()

    response = client.post(
        "/documents",
        files={"file": ("test_image.png", sample_png_bytes, "image/png")},
        data={"document_name": "Test Diagram"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["mime_type"] == "image/png"
    assert data["original_document_hash"] == expected_hash

def test_document_list(client: TestClient, sample_pdf_bytes: bytes):
    client.post(
        "/documents",
        files={"file": ("list_test.pdf", sample_pdf_bytes, "application/pdf")},
        data={"document_name": "List Test"}
    )
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["documents"]) >= 1

def test_document_not_found(client: TestClient):
    response = client.get("/documents/doc_nonexistent_99999")
    assert response.status_code == 404
    error_data = response.json()
    assert error_data["error"]["code"] == "DOCUMENT_NOT_FOUND"
