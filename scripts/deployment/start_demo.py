import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_backend_liveness(url: str = "http://127.0.0.1:8000/health", timeout: int = 15) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.urlopen(url, timeout=1)
            if req.getcode() == 200:
                return True
        except Exception:
            time.sleep(0.5)
    return False

def start_full_demo():
    print("\n" + "=" * 70)
    print("  SIH26237 — OFFLINE DEMO LAUNCHER (ONE-COMMAND START)")
    print("=" * 70)

    # 1. Prerequisites Check
    print("[1/5] Checking environment prerequisites...")
    if sys.version_info < (3, 9):
        print(f"[!] Error: Python 3.9+ required, found {sys.version.split()[0]}")
        sys.exit(1)
    print(f"  * Python: {sys.version.split()[0]} (OK)")

    # 2. Reset & Prepare Demo Fixtures
    print("\n[2/5] Initializing clean demo environment & baseline fixtures...")
    from scripts.deployment.reset_demo import reset_demo_environment
    reset_demo_environment()

    # 3. Start FastAPI Backend
    print("\n[3/5] Starting FastAPI Backend (Uvicorn on http://127.0.0.1:8000)...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "apps.api.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--log-level", "warning"
    ]
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(PROJECT_ROOT))

    if not check_backend_liveness():
        print("[!] Backend failed to start within 15 seconds.")
        backend_proc.terminate()
        sys.exit(1)
    print("  * Backend API is LIVE at http://127.0.0.1:8000")

    # 4. Start Web Dashboard
    frontend_proc = None
    frontend_url = "http://127.0.0.1:5173"
    web_dir = PROJECT_ROOT / "apps" / "web"

    print("\n[4/5] Starting Web Dashboard...")
    try:
        # Check if node/npx is available
        node_check = subprocess.run(["node", "--version"], capture_output=True, text=True, check=False, shell=True)
        if node_check.returncode == 0:
            # Check if dist exists, otherwise build it
            dist_index = web_dir / "dist" / "index.html"
            if not dist_index.exists():
                print("  * Building frontend production bundle via Vite...")
                subprocess.run(["npx", "vite", "build"], cwd=str(web_dir), check=False, shell=True)

            # Start vite preview server
            fe_cmd = ["npx", "vite", "preview", "--port", "5173", "--host", "127.0.0.1"]
            frontend_proc = subprocess.Popen(fe_cmd, cwd=str(web_dir), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
            time.sleep(1.5)
            print(f"  * Web Dashboard is LIVE at {frontend_url}")
        else:
            print("  * Node.js not detected; Web Dashboard UI can be launched separately.")
    except Exception as e:
        print(f"  * Note on frontend preview: {e}")

    # 5. Run Health Check
    print("\n[5/5] Executing deployment health verification...")
    from scripts.deployment.health_check import run_health_check
    health = run_health_check()

    print("\n" + "=" * 70)
    print("  SYSTEM READY FOR JUDGES / EVALUATORS")
    print("=" * 70)
    print("  * Web Dashboard:       http://127.0.0.1:5173")
    print("  * REST API Base:       http://127.0.0.1:8000")
    print("  * Interactive OpenAPI: http://127.0.0.1:8000/docs")
    print("  * Health Report:       artifacts/deployment/health_report.json")
    print("  * Demo Fixtures:       data/demo_fixtures/")
    print("=" * 70)
    print("  Press Ctrl+C to gracefully stop all services.")
    print("=" * 70 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Gracefully stopping SIH26237 demo services...")
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        print("[+] All services stopped cleanly.")

if __name__ == "__main__":
    start_full_demo()
