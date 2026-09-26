import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.deployment.generate_demo_fixtures import generate_fixtures
from apps.api.config import config

def reset_demo_environment() -> bool:
    print("=" * 60)
    print("SIH26237 DEMO ENVIRONMENT RESET")
    print("=" * 60)

    data_dir = config.data_dir
    artifacts_dir = config.artifacts_dir
    db_file = config.db_path
    fixtures_dir = data_dir / "demo_fixtures"

    print(f"[*] Target Data Directory: {data_dir}")

    # 1. Purge SQLite database
    if db_file.exists():
        try:
            db_file.unlink()
            print(f"[+] Purged SQLite database: {db_file.name}")
        except Exception as e:
            print(f"[!] Warning: Could not delete {db_file.name}: {e}")

    # 2. Purge Data Plane artifacts
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir, ignore_errors=True)
        print(f"[+] Purged artifact storage: {artifacts_dir.name}/")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # 3. Purge and regenerate demo fixtures
    if fixtures_dir.exists():
        shutil.rmtree(fixtures_dir, ignore_errors=True)
        print(f"[+] Purged demo fixtures: {fixtures_dir.name}/")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # 4. Regenerate baseline fixtures
    manifest = generate_fixtures(fixtures_dir)
    print(f"[+] Regenerated baseline fixtures: {len(manifest.get('fixtures', []))} scenarios")

    print("[+] Demo environment successfully reset to PRISTINE state.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    reset_demo_environment()
