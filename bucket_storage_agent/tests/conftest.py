"""
Shared config for all test files.
Run setup_test_environment.py once before executing any test.
"""

PROJECT_ID        = "health-data-platform12345"
TEST_BUCKET_MAIN  = "ngoga-test-main"
TEST_BUCKET_BACKUP= "ngoga-test-backup"
TEST_BUCKET_WEBSITE="ngoga-test-website"
TEST_BUCKET_ARCHIVE="ngoga-test-archive"
BIGQUERY_DATASET  = "storage_analytics"
BIGQUERY_TABLE    = "bucket_events"
AGENT_URL         = "http://localhost:8080"

import httpx, json, sys

def ask(instruction: str) -> str:
    """Send a natural language instruction to the running agent."""
    try:
        r = httpx.post(f"{AGENT_URL}/api/chat",
                       json={"message": instruction},
                       timeout=120)
        r.raise_for_status()
        return r.json().get("response", "")
    except httpx.ConnectError:
        print("ERROR: FastAPI not running. Start it first:")
        print("  uvicorn bucket_storage_agent.app:app --host 0.0.0.0 --port 8080 --reload")
        sys.exit(1)

def run_test(name: str, instruction: str):
    print(f"\n[TEST] {name}")
    print(f"  > {instruction}")
    result = ask(instruction)
    print(f"  < {result[:300]}{'...' if len(result) > 300 else ''}")
    return result
