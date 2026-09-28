import os
import sys

# Pre-initialize cryptography on Windows to ensure correct OpenSSL DLL resolution
try:
    import cryptography
    import cryptography.hazmat.primitives.ciphers
except ImportError:
    pass

# Ensure repository root is on sys.path for test execution
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import pytest

@pytest.fixture(autouse=True)
def _reset_api_state():
    try:
        from apps.api.security import default_rate_limiter, default_replay_cache
        default_rate_limiter.reset()
        default_replay_cache.reset()
    except Exception:
        pass
    yield
    try:
        from apps.api.security import default_rate_limiter, default_replay_cache
        default_rate_limiter.reset()
        default_replay_cache.reset()
    except Exception:
        pass


