import os
import sys
from pathlib import Path
import uvicorn

# Ensure repository root is on Python module search path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Set demo environment variables for SIH evaluation
os.environ.setdefault("DEMO_AUTH_ENABLED", "true")
os.environ.setdefault("DEMO_USERNAME", "admin")
os.environ.setdefault("DEMO_PASSWORD", "admin")
os.environ.setdefault("SIH_HOST", "0.0.0.0")
os.environ.setdefault("CORS_ORIGINS", "*")

# Import the core AegisTrace FastAPI application
from apps.api.main import app

import gradio as gr
# Mount FastAPI as root application and Gradio blocks
demo = gr.mount_gradio_app(app, gr.Blocks(title="AegisTrace"), path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
