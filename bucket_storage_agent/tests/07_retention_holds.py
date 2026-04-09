"""
TEST FILE 07 — Retention Policies & Object Holds (8 tools)
===========================================================
Tools tested:
  54. set_retention_policy
  55. get_retention_policy
  56. remove_retention_policy
  57. set_temporary_hold
  58. release_temporary_hold
  59. set_event_based_hold
  60. release_event_based_hold
  61. set_default_event_based_hold

Run: python bucket_storage_agent/tests/07_retention_holds.py
Requires: FastAPI running on port 8080
Note: Retention policies cannot be reduced once set.
      This test uses a short 1-second retention for safety.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import run_test, TEST_BUCKET_MAIN

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST SUITE 07: Retention Policies & Object Holds")
    print("="*60)

    # Tool 54: set_retention_policy
    run_test(
        "set_retention_policy",
        f"Set a retention policy of 1 second on bucket '{TEST_BUCKET_MAIN}' for testing purposes"
    )

    # Tool 55: get_retention_policy
    run_test(
        "get_retention_policy",
        f"Show me the current retention policy for bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 56: remove_retention_policy
    run_test(
        "remove_retention_policy",
        f"Remove the retention policy from bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 57: set_temporary_hold
    run_test(
        "set_temporary_hold",
        f"Set a temporary hold on object 'test.txt' in bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 58: release_temporary_hold
    run_test(
        "release_temporary_hold",
        f"Release the temporary hold on object 'test.txt' in bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 59: set_event_based_hold
    run_test(
        "set_event_based_hold",
        f"Set an event-based hold on object 'document.pdf' in bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 60: release_event_based_hold
    run_test(
        "release_event_based_hold",
        f"Release the event-based hold on object 'document.pdf' in bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 61: set_default_event_based_hold
    run_test(
        "set_default_event_based_hold",
        f"Enable default event-based hold for all new objects in bucket '{TEST_BUCKET_MAIN}'"
    )

    # Disable the default hold to leave the bucket in a clean state
    run_test(
        "disable default event-based hold (cleanup)",
        f"Disable default event-based hold for bucket '{TEST_BUCKET_MAIN}'"
    )

    print("\n✓ Suite 07 complete.\n")
