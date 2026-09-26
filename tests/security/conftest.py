import pytest
import base64
from fastapi.testclient import TestClient
from apps.api.main import app
from demo.end_to_end import create_sample_pdf
from core.recipient import default_registry
from core.release import default_release_manager
from core.ledger.ledger import default_ledger
from core.attribution.engine import default_attribution_engine

@pytest.fixture(scope="session")
def client():
    # Ensure demo recipients are initialized
    default_registry.init_demo_recipients()
    return TestClient(app)

@pytest.fixture
def sample_pdf_bytes():
    return create_sample_pdf()

@pytest.fixture
def sample_pdf_b64(sample_pdf_bytes):
    return base64.b64encode(sample_pdf_bytes).decode('utf-8')
