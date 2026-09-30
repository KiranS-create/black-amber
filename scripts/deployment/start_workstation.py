"""
AegisTrace (SIH26237) — One-Click Forensic Workstation Launcher
Launches FastAPI backend (port 8000) and React frontend (port 3000) concurrently,
verifies prerequisites and health, and opens the workstation in the default browser.
"""

import os
import signal
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_service_ready(url: str, timeout: int = 20) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.urlopen(url, timeout=1)
            if req.getcode() in (200, 304, 404):
                return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    print("\n" + "=" * 76)
    print("  AEGISTRACE (SIH26237) — FORENSIC WORKSTATION ONE-CLICK LAUNCHER")
    print("  Code Name: Black Amber | Post-Quantum Document Attribution Engine")
    print("=" * 76)

    # 1. Environment & Prerequisites
    print("\n[1/4] Checking system prerequisites...")
    if sys.version_info < (3, 9):
        print(f"  [X] Error: Python 3.9+ required, found {sys.version.split()[0]}")
        sys.exit(1)
    print(f"  * Python: {sys.version.split()[0]} (OK)")

    try:
        node_res = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            shell=True
        )
        if node_res.returncode == 0:
            print(f"  * Node.js: {node_res.stdout.strip()} (OK)")
        else:
            print("  [!] Warning: Node.js command returned non-zero. Check Node.js installation.")
    except Exception as e:
        print(f"  [!] Warning: Could not detect Node.js: {e}")

    # Set demo authentication
    os.environ["DEMO_AUTH_ENABLED"] = "true"

    # 2. Launch Backend API
    print("\n[2/4] Starting FastAPI Backend on http://127.0.0.1:8000...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "apps.api.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--log-level", "warning"
    ]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(PROJECT_ROOT),
        env=os.environ.copy()
    )

    if not check_service_ready("http://127.0.0.1:8000/health", timeout=15):
        print("  [X] Backend failed to report healthy on port 8000.")
        backend_proc.terminate()
        sys.exit(1)
    print("  * Backend API is LIVE at http://127.0.0.1:8000 (Health OK)")

    # 3. Launch Frontend Web Application
    web_dir = PROJECT_ROOT / "apps" / "web"
    print("\n[3/4] Starting React Forensic Workstation on http://localhost:3000...")
    
    # Use npx vite for direct execution
    frontend_cmd = "npx vite --port 3000 --host 127.0.0.1"
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(web_dir),
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    if not check_service_ready("http://127.0.0.1:3000", timeout=20):
        print("  [!] Frontend preview taking longer than expected. Continuing to launch...")
    else:
        print("  * Frontend Workstation is LIVE at http://localhost:3000")

    # 4. Open Workstation in Browser
    print("\n[4/4] Opening default web browser to workstation...")
    try:
        webbrowser.open("http://localhost:3000")
    except Exception as e:
        print(f"  [!] Browser open note: {e}")

    print("\n" + "=" * 76)
    print("  AEGISTRACE FORENSIC WORKSTATION IS READY FOR EVALUATION")
    print("=" * 76)
    print("  * Dashboard UI:        http://localhost:3000")
    print("  * REST API Engine:     http://127.0.0.1:8000")
    print("  * Interactive OpenAPI: http://127.0.0.1:8000/docs")
    print("  * Demo Credentials:    admin / admin  OR  op_a / password123")
    print("=" * 76)
    print("  Press Ctrl+C to cleanly stop all workstation processes.\n")

    def signal_handler(sig, frame):
        print("\n[*] Stopping AegisTrace workstation services...")
        try:
            frontend_proc.terminate()
        except Exception:
            pass
        try:
            backend_proc.terminate()
        except Exception:
            pass
        print("[+] All services stopped cleanly. Exiting.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            time.sleep(1)
            # Monitor if any process died unexpectedly
            if backend_proc.poll() is not None:
                print("\n[!] Backend process exited unexpectedly.")
                break
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
