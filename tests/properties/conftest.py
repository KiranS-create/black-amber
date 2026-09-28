"""
tests/properties/conftest.py

Fixtures and configuration for property-based and fuzzing test suites.
"""

import sys
from pathlib import Path
import pytest

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.testing.property_engine import PropertyRunner, DeterministicGenerator


@pytest.fixture
def runner() -> PropertyRunner:
    return PropertyRunner(default_seed=20260927)


@pytest.fixture
def gen() -> DeterministicGenerator:
    return DeterministicGenerator(seed=133742)
