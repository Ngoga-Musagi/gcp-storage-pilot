"""
TEST FILE 03 — Permissions & IAM (10 tools)
============================================
Tools tested:
  19. add_bucket_member
  20. remove_bucket_member
  21. list_bucket_permissions
  22. enable_public_access
  23. disable_public_access
  24. get_bucket_policy
  25. set_bucket_policy
  26. get_bucket_iam_policy
  27. set_bucket_iam_policy
  28. set_uniform_bucket_level_access

Run: python bucket_storage_agent/tests/03_permissions.py
Requires: FastAPI running on port 8080
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import run_test, TEST_BUCKET_MAIN, PROJECT_ID

# Use your own service account email here
SA_EMAIL = f"storage-agent@{PROJECT_ID}.iam.gserviceaccount.com"

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST SUITE 03: Permissions & IAM")
    print("="*60)

    # Tool 19: add_bucket_member
    run_test(
        "add_bucket_member",
        f"Add service account '{SA_EMAIL}' as a Storage Object Viewer to '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 20: list_bucket_permissions
    run_test(
        "list_bucket_permissions",
        f"List all users and service accounts that have access to '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 21: remove_bucket_member
    run_test(
        "remove_bucket_member",
        f"Remove service account '{SA_EMAIL}' from '{TEST_BUCKET_MAIN}' bucket permissions"
    )

    # Tool 22: enable_public_access
    run_test(
        "enable_public_access",
        f"Enable public read access for '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 23: disable_public_access
    run_test(
        "disable_public_access",
        f"Disable public access for '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 24: get_bucket_policy
    run_test(
        "get_bucket_policy",
        f"Get the current bucket policy for '{TEST_BUCKET_MAIN}'"
    )

    # Tool 25: set_bucket_policy
    run_test(
        "set_bucket_policy",
        f"Set the bucket policy for '{TEST_BUCKET_MAIN}' to prevent public access"
    )

    # Tool 26: get_bucket_iam_policy
    run_test(
        "get_bucket_iam_policy",
        f"Show me the full IAM policy for '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 27: set_bucket_iam_policy
    run_test(
        "set_bucket_iam_policy",
        f"Set IAM policy for '{TEST_BUCKET_MAIN}' to grant Storage Object Viewer to allUsers (public read)"
    )

    # Revert public access after test
    run_test(
        "disable_public_access (revert)",
        f"Disable public access for '{TEST_BUCKET_MAIN}' bucket"
    )

    # Tool 28: set_uniform_bucket_level_access
    run_test(
        "set_uniform_bucket_level_access",
        f"Enable uniform bucket-level access (UBLA) for '{TEST_BUCKET_MAIN}' bucket"
    )

    print("\n✓ Suite 03 complete.\n")
