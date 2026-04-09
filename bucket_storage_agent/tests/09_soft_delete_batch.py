"""
TEST FILE 09 — Soft Delete, Batch Ops, Resumable Upload & Inventory (10 tools)
===============================================================================
Tools tested:
  68. enable_soft_delete
  69. disable_soft_delete
  70. list_soft_deleted_objects
  71. restore_soft_deleted_object
  72. batch_delete_objects
  73. batch_copy_objects
  74. compose_objects
  75. upload_large_object_resumable
  76. create_inventory_report
  77. list_inventory_reports

Run: python bucket_storage_agent/tests/09_soft_delete_batch.py
Requires: FastAPI running on port 8080
Prerequisites: setup_test_environment.py already run (test_data/large_test.bin exists — 5 MB)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import run_test, TEST_BUCKET_MAIN, TEST_BUCKET_BACKUP

TEST_DATA = Path(__file__).parent.parent / "test_data"

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST SUITE 09: Soft Delete, Batch Ops, Resumable Upload & Inventory")
    print("="*60)

    # ── Soft Delete ────────────────────────────────────────────────
    print("\n--- Soft Delete ---")

    # Tool 68: enable_soft_delete
    run_test(
        "enable_soft_delete",
        f"Enable soft delete on bucket '{TEST_BUCKET_MAIN}' with a 7-day retention duration"
    )

    # Delete an object to create a soft-deleted version
    run_test(
        "delete object to test soft delete",
        f"Delete the file 'style.css' from bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 70: list_soft_deleted_objects
    run_test(
        "list_soft_deleted_objects",
        f"List all soft-deleted objects in bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 71: restore_soft_deleted_object
    run_test(
        "restore_soft_deleted_object",
        f"Restore the soft-deleted object 'style.css' in bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 69: disable_soft_delete
    run_test(
        "disable_soft_delete",
        f"Disable soft delete on bucket '{TEST_BUCKET_MAIN}'"
    )

    # ── Batch Operations ───────────────────────────────────────────
    print("\n--- Batch Operations ---")

    # Tool 73: batch_copy_objects
    run_test(
        "batch_copy_objects",
        f"Batch copy all objects matching prefix 'test' from bucket '{TEST_BUCKET_MAIN}' to bucket '{TEST_BUCKET_BACKUP}'"
    )

    # Tool 74: compose_objects
    run_test(
        "compose_objects",
        f"Compose objects 'test.txt' and 'style.css' from bucket '{TEST_BUCKET_MAIN}' into a new object called 'composed-output.txt'"
    )

    # Tool 72: batch_delete_objects
    run_test(
        "batch_delete_objects",
        f"Batch delete all objects matching prefix 'test' from bucket '{TEST_BUCKET_BACKUP}'"
    )

    # ── Resumable Upload ───────────────────────────────────────────
    print("\n--- Resumable Upload ---")

    # Tool 75: upload_large_object_resumable
    run_test(
        "upload_large_object_resumable",
        f"Upload the large file '{TEST_DATA / 'large_test.bin'}' to bucket '{TEST_BUCKET_MAIN}' using resumable upload as 'large_test.bin'"
    )

    # ── Inventory Reports ──────────────────────────────────────────
    print("\n--- Inventory Reports ---")

    # Tool 76: create_inventory_report
    run_test(
        "create_inventory_report",
        f"Create an inventory report for bucket '{TEST_BUCKET_MAIN}' and store the results in bucket '{TEST_BUCKET_BACKUP}'"
    )

    # Tool 77: list_inventory_reports
    run_test(
        "list_inventory_reports",
        f"List all inventory reports configured for bucket '{TEST_BUCKET_MAIN}'"
    )

    print("\n✓ Suite 09 complete.\n")
