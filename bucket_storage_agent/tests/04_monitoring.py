"""
TEST FILE 04 — Monitoring & Optimization (8 tools)
===================================================
Tools tested:
  29. view_bucket_metrics
  30. view_bucket_cost_estimate
  31. monitor_access_logs
  32. enable_request_logging
  33. disable_request_logging
  34. analyze_bucket_activity
  35. summarize_bucket_status
  36. recommend_storage_class

Run: python bucket_storage_agent/tests/04_monitoring.py
Requires: FastAPI running on port 8080
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import run_test, TEST_BUCKET_MAIN

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST SUITE 04: Monitoring & Optimization")
    print("="*60)

    # Tool 29: view_bucket_metrics
    run_test(
        "view_bucket_metrics",
        f"Show me the metrics for '{TEST_BUCKET_MAIN}' bucket over the last 7 days"
    )

    # Tool 30: view_bucket_cost_estimate
    run_test(
        "view_bucket_cost_estimate",
        f"Analyze the cost estimate for '{TEST_BUCKET_MAIN}' bucket for the next month"
    )

    # Tool 31: monitor_access_logs
    run_test(
        "monitor_access_logs",
        f"Monitor access logs for '{TEST_BUCKET_MAIN}' bucket for the last 24 hours"
    )

    # Tool 32: enable_request_logging
    run_test(
        "enable_request_logging",
        f"Enable request logging for '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 33: disable_request_logging
    run_test(
        "disable_request_logging",
        f"Disable request logging for '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 34: analyze_bucket_activity
    run_test(
        "analyze_bucket_activity",
        f"Analyze the activity patterns for '{TEST_BUCKET_MAIN}' bucket over the last 30 days"
    )

    # Tool 35: summarize_bucket_status
    run_test(
        "summarize_bucket_status",
        f"Summarize the current status of '{TEST_BUCKET_MAIN}' bucket including usage, costs, and configuration"
    )

    # Tool 36: recommend_storage_class
    run_test(
        "recommend_storage_class",
        f"Analyze '{TEST_BUCKET_MAIN}' bucket and recommend the most cost-effective storage class for my files"
    )

    print("\n✓ Suite 04 complete.\n")
