"""
TEST FILE 05 — Website Hosting (7 tools)
=========================================
Tools tested:
  37. enable_website_hosting
  38. set_website_main_page
  39. set_website_error_page
  40. set_cors_configuration
  41. set_cache_control
  42. upload_website_assets
  43. disable_website_hosting

Run: python bucket_storage_agent/tests/05_website_hosting.py
Requires: FastAPI running on port 8080
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import run_test, TEST_BUCKET_WEBSITE

TEST_DATA = Path(__file__).parent.parent / "test_data"

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST SUITE 05: Website Hosting")
    print("="*60)

    # Tool 37: enable_website_hosting
    run_test(
        "enable_website_hosting",
        f"Enable static website hosting for '{TEST_BUCKET_WEBSITE}' bucket with index.html as the main page and 404.html as the error page"
    )

    # Tool 38: set_website_main_page
    run_test(
        "set_website_main_page",
        f"Set the main page for '{TEST_BUCKET_WEBSITE}' website to 'index.html'"
    )

    # Tool 39: set_website_error_page
    run_test(
        "set_website_error_page",
        f"Set the error page for '{TEST_BUCKET_WEBSITE}' website to '404.html'"
    )

    # Tool 40: set_cors_configuration
    run_test(
        "set_cors_configuration",
        f"Set CORS configuration for '{TEST_BUCKET_WEBSITE}' bucket to allow GET and HEAD requests from any origin with a max age of 3600 seconds"
    )

    # Tool 41: set_cache_control
    run_test(
        "set_cache_control",
        f"Set cache control for 'style.css' in '{TEST_BUCKET_WEBSITE}' bucket to 'public, max-age=3600'"
    )

    # Tool 42: upload_website_assets
    run_test(
        "upload_website_assets",
        f"Upload all files from '{TEST_DATA}' folder to '{TEST_BUCKET_WEBSITE}' bucket"
    )

    # Verify the website is publicly accessible
    run_test(
        "verify website URL",
        f"Show me the public website URL for '{TEST_BUCKET_WEBSITE}' bucket"
    )

    # Tool 43: disable_website_hosting
    run_test(
        "disable_website_hosting",
        f"Disable website hosting for '{TEST_BUCKET_WEBSITE}' bucket"
    )

    print("\n✓ Suite 05 complete.\n")
