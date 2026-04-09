"""
TEST FILE 02 — Object Operations (10 tools)
============================================
Tools tested:
  9.  upload_object
  10. list_objects
  11. get_object_metadata
  12. download_object
  13. copy_object
  14. rename_object
  15. generate_signed_url
  16. update_object_metadata
  17. restore_object_version
  18. delete_object

Run: python bucket_storage_agent/tests/02_object_ops.py
Requires: FastAPI running on port 8080
Prerequisites: setup_test_environment.py already run (test files exist in test_data/)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import run_test, TEST_BUCKET_MAIN, TEST_BUCKET_BACKUP

TEST_DATA = Path(__file__).parent.parent / "test_data"

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST SUITE 02: Object Operations")
    print("="*60)

    # Tool 9: upload_object
    run_test(
        "upload_object",
        f"Upload the file '{TEST_DATA / 'test.txt'}' to the bucket '{TEST_BUCKET_MAIN}' as 'uploaded-test.txt'"
    )

    # Tool 10: list_objects
    run_test(
        "list_objects",
        f"List all objects in '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 11: get_object_metadata
    run_test(
        "get_object_metadata",
        f"Show me detailed metadata for the file 'test.txt' in '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 12: download_object
    run_test(
        "download_object",
        f"Download the file 'test.txt' from '{TEST_BUCKET_MAIN}' bucket to '{TEST_DATA / 'downloaded-test.txt'}'"
    )

    # Tool 13: copy_object
    run_test(
        "copy_object",
        f"Copy the file 'test.txt' from '{TEST_BUCKET_MAIN}' to '{TEST_BUCKET_BACKUP}'"
    )

    # Tool 14: rename_object
    run_test(
        "rename_object",
        f"Rename the file 'uploaded-test.txt' to 'renamed-test.txt' in '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 15: generate_signed_url
    run_test(
        "generate_signed_url",
        f"Generate a signed URL for 'test.txt' in '{TEST_BUCKET_MAIN}' that expires in 2 hours"
    )

    # Tool 16: update_object_metadata
    run_test(
        "update_object_metadata",
        f"Update the metadata for 'test.txt' in '{TEST_BUCKET_MAIN}' to set content-type as 'text/plain' and add custom metadata 'author=Ngoga'"
    )

    # Tool 17: restore_object_version (requires versioning — enabled in suite 01)
    run_test(
        "restore_object_version",
        f"Restore the previous version of 'test.txt' in '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 18: delete_object
    run_test(
        "delete_object",
        f"Delete the file 'renamed-test.txt' from '{TEST_BUCKET_MAIN}' bucket"
    )

    print("\n✓ Suite 02 complete.\n")
