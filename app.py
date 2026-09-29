import os
import sys
from pathlib import Path
import uvicorn

# Ensure repository root is on Python module search path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Set demo environment variables for SIH evaluation if not present
os.environ.setdefault("DEMO_AUTH_ENABLED", "true")
os.environ.setdefault("DEMO_USERNAME", "admin")
os.environ.setdefault("DEMO_PASSWORD", "admin")
os.environ.setdefault("SIH_HOST", "0.0.0.0")
os.environ.setdefault("CORS_ORIGINS", "*")

# Import the core AegisTrace FastAPI application
from apps.api.main import app

try:
    import gradio as gr
    # Mount FastAPI to Gradio Blocks for Hugging Face Spaces Gradio runner
    demo = gr.mount_gradio_app(app, gr.Blocks(title="AegisTrace"), path="/gradio")
except Exception:
    demo = app

if __name__ == "__main__":
    # Hugging Face Spaces standard port is 7860; Render/Koyeb uses $PORT or 8000
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
