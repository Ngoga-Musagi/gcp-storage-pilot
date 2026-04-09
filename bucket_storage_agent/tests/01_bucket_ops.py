"""
TEST FILE 01 — Bucket Operations (8 tools)
==========================================
Tools tested:
  1.  create_storage_bucket
  2.  list_storage_buckets
  3.  get_bucket_details
  4.  update_bucket_configuration
  5.  enable_versioning
  6.  disable_versioning
  7.  view_bucket_usage
  8.  delete_storage_bucket

Run: python bucket_storage_agent/tests/01_bucket_ops.py
Requires: FastAPI running on port 8080
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import run_test, TEST_BUCKET_MAIN

TEMP_BUCKET = "ngoga-temp-test-bucket"

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST SUITE 01: Bucket Operations")
    print("="*60)

    # Tool 1: create_storage_bucket
    run_test(
        "create_storage_bucket",
        f"Create a new storage bucket named '{TEMP_BUCKET}' in the US region with STANDARD storage class"
    )

    # Tool 2: list_storage_buckets
    run_test(
        "list_storage_buckets",
        "List all storage buckets in my project"
    )

    # Tool 3: get_bucket_details
    run_test(
        "get_bucket_details",
        f"Get detailed information about the bucket '{TEST_BUCKET_MAIN}' including location, storage class, and labels"
    )

    # Tool 4: update_bucket_configuration
    run_test(
        "update_bucket_configuration",
        f"Update the storage class of '{TEMP_BUCKET}' bucket to NEARLINE"
    )

    # Tool 5: enable_versioning
    run_test(
        "enable_versioning",
        f"Enable versioning for the bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 6: disable_versioning
    run_test(
        "disable_versioning",
        f"Disable versioning for the bucket '{TEMP_BUCKET}'"
    )

    # Tool 7: view_bucket_usage
    run_test(
        "view_bucket_usage",
        f"Show me the usage statistics for '{TEST_BUCKET_MAIN}' bucket including size and object count"
    )

    # Tool 8: delete_storage_bucket (clean up temp)
    run_test(
        "delete_storage_bucket",
        f"Delete the bucket '{TEMP_BUCKET}' and all its contents"
    )

    print("\n✓ Suite 01 complete.\n")
