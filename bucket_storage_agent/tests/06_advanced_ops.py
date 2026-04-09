"""
TEST FILE 06 — Advanced Operations (9 tools)
=============================================
Tools tested:
  44. add_bucket_label
  45. remove_bucket_label
  46. set_bucket_lifecycle_rules
  47. audit_bucket_access
  48. sync_local_directory_to_bucket
  49. backup_bucket_to_another_bucket
  50. archive_old_objects
  51. schedule_periodic_cleanup
  52. migrate_bucket_to_different_region
  53. trigger_cloud_function_on_event

Run: python bucket_storage_agent/tests/06_advanced_ops.py
Requires: FastAPI running on port 8080
Note: migrate_bucket_to_different_region may take several minutes
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import run_test, TEST_BUCKET_MAIN, TEST_BUCKET_BACKUP, TEST_BUCKET_ARCHIVE

TEST_DATA = Path(__file__).parent.parent / "test_data"

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST SUITE 06: Advanced Operations")
    print("="*60)

    # Tool 44: add_bucket_label
    run_test(
        "add_bucket_label",
        f"Add a label 'environment=testing' to the bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 45: remove_bucket_label
    run_test(
        "remove_bucket_label",
        f"Remove the label 'environment' from the bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 46: set_bucket_lifecycle_rules
    run_test(
        "set_bucket_lifecycle_rules",
        f"Set lifecycle rules for '{TEST_BUCKET_MAIN}' to automatically move objects older than 30 days to NEARLINE and delete objects older than 365 days"
    )

    # Tool 47: audit_bucket_access
    run_test(
        "audit_bucket_access",
        f"Audit the access patterns and security settings for '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 48: sync_local_directory_to_bucket
    run_test(
        "sync_local_directory_to_bucket",
        f"Sync my local directory '{TEST_DATA}' to '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 49: backup_bucket_to_another_bucket
    run_test(
        "backup_bucket_to_another_bucket",
        f"Backup all contents from '{TEST_BUCKET_MAIN}' bucket to '{TEST_BUCKET_BACKUP}'"
    )

    # Tool 50: archive_old_objects
    run_test(
        "archive_old_objects",
        f"Archive objects older than 1 day in '{TEST_BUCKET_ARCHIVE}' bucket to COLDLINE storage"
    )

    # Tool 51: schedule_periodic_cleanup
    run_test(
        "schedule_periodic_cleanup",
        f"Schedule periodic cleanup for '{TEST_BUCKET_MAIN}' bucket to delete temporary files older than 7 days"
    )

    # Tool 52: migrate_bucket_to_different_region
    # NOTE: This creates a new bucket — use a small dedicated test bucket
    run_test(
        "migrate_bucket_to_different_region",
        f"Migrate '{TEST_BUCKET_ARCHIVE}' bucket contents to a new bucket in the EU region"
    )

    # Tool 53: trigger_cloud_function_on_event
    run_test(
        "trigger_cloud_function_on_event",
        f"Set up a Cloud Function trigger for '{TEST_BUCKET_MAIN}' bucket to fire when new files are uploaded — use function name 'process-upload'"
    )

    print("\n✓ Suite 06 complete.\n")
