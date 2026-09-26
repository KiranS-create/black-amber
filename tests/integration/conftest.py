import os
import io
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.config import config
from apps.api.storage import FilesystemArtifactStorage, MetadataRepository
from apps.api.orchestrator import SystemOrchestrator, default_orchestrator
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.ledger.ledger import TamperEvidentLedger
from core.traceability.provider import PrototypeTraceabilityProvider
from core.attribution.engine import AttributionEngine
from demo.end_to_end import create_sample_pdf

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture
def sample_pdf_bytes():
    return create_sample_pdf("INTEGRATION TEST CLASSIFIED SPEC - SIH26237")

@pytest.fixture
def sample_png_bytes():
    # 1x1 valid PNG bytes
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
