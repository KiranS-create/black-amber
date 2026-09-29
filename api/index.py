import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Set demo environment variables for SIH evaluation
os.environ.setdefault("DEMO_AUTH_ENABLED", "true")
os.environ.setdefault("DEMO_USERNAME", "admin")
os.environ.setdefault("DEMO_PASSWORD", "admin")
os.environ.setdefault("SIH_HOST", "0.0.0.0")
os.environ.setdefault("CORS_ORIGINS", "*")

from apps.api.main import app
