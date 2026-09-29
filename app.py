import os
import sys
from pathlib import Path
import uvicorn
import gradio as gr

# ZeroGPU requires a registered Gradio event function with @spaces.GPU
try:
    import spaces
    @spaces.GPU
    def _zero_gpu_worker(payload: str) -> str:
        return payload
except Exception:
    def _zero_gpu_worker(payload: str) -> str:
        return payload

# Build minimal Blocks with ZeroGPU handler
with gr.Blocks(title="AegisTrace") as demo_blocks:
    _inp = gr.Textbox(visible=False)
    _out = gr.Textbox(visible=False)
    _btn = gr.Button("Init", visible=False)
    _btn.click(_zero_gpu_worker, inputs=_inp, outputs=_out)

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

# Mount FastAPI as root application and Gradio blocks for ZeroGPU
demo = gr.mount_gradio_app(app, demo_blocks, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
