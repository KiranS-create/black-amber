import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.main import app

@pytest.fixture(scope="session")
def client():
    return TestClient(app)
