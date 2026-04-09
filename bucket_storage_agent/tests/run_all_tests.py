"""
Run all 10 test suites in sequence.

Usage:
    python bucket_storage_agent/tests/run_all_tests.py
    python bucket_storage_agent/tests/run_all_tests.py --suite 05   # run one suite only

Requires:
  1. setup_test_environment.py already run
  2. FastAPI running:  uvicorn bucket_storage_agent.app:app --host 0.0.0.0 --port 8080 --reload
"""

import sys
import subprocess
from pathlib import Path

TESTS_DIR = Path(__file__).parent
SUITES = [
    "01_bucket_ops.py",
    "02_object_ops.py",
    "03_permissions.py",
    "04_monitoring.py",
    "05_website_hosting.py",
    "06_advanced_ops.py",
    "07_retention_holds.py",
    "08_encryption_pubsub.py",
    "09_soft_delete_batch.py",
    "10_bigquery_intelligence.py",
]

def run_suite(filename: str) -> bool:
    path = TESTS_DIR / filename
    print(f"\n{'='*60}")
    print(f"Running: {filename}")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(TESTS_DIR.parent.parent),
    )
    return result.returncode == 0

if __name__ == "__main__":
    # Optional: run single suite via --suite 05
    if "--suite" in sys.argv:
        idx = sys.argv.index("--suite")
        prefix = sys.argv[idx + 1].zfill(2)
        target = next((s for s in SUITES if s.startswith(prefix)), None)
        if not target:
            print(f"ERROR: No suite matching prefix '{prefix}'")
            sys.exit(1)
        run_suite(target)
        sys.exit(0)

    passed, failed = [], []
    for suite in SUITES:
        ok = run_suite(suite)
        (passed if ok else failed).append(suite)

    print(f"\n{'='*60}")
    print(f"RESULTS: {len(passed)} passed, {len(failed)} failed")
    if failed:
        print("Failed suites:")
        for f in failed:
            print(f"  ✗ {f}")
    else:
        print("All suites passed ✓")
    print(f"{'='*60}\n")
