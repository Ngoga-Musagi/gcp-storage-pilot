"""
Test Environment Setup
======================
Run this ONCE before running any tests.
Creates all required GCP resources for testing all 81 tools.

Usage:
    python bucket_storage_agent/setup_test_environment.py
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv("bucket_storage_agent/.env")

from google.cloud import storage, bigquery
from google.auth import default
from google.api_core.exceptions import AlreadyExists, Conflict

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "health-data-platform12345")
CREDS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# ── Test resource names (used across all test files) ──────────────────────────
TEST_BUCKET_MAIN    = "ngoga-test-main"
TEST_BUCKET_BACKUP  = "ngoga-test-backup"
TEST_BUCKET_WEBSITE = "ngoga-test-website"
TEST_BUCKET_ARCHIVE = "ngoga-test-archive"
BIGQUERY_DATASET    = "storage_analytics"
BIGQUERY_TABLE      = "bucket_events"
TEST_FILES_DIR      = Path(__file__).parent / "test_data"
# ─────────────────────────────────────────────────────────────────────────────


def get_clients():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDS_PATH
    credentials, _ = default()
    gcs = storage.Client(project=PROJECT_ID, credentials=credentials)
    bq  = bigquery.Client(project=PROJECT_ID, credentials=credentials)
    return gcs, bq, credentials


def create_bucket(gcs, name, location="US"):
    try:
        bucket = gcs.create_bucket(name, location=location)
        print(f"  ✓ Bucket created: {name}")
        return bucket
    except Conflict:
        print(f"  ✓ Bucket already exists: {name}")
        return gcs.bucket(name)


def create_bigquery_dataset(bq):
    dataset_id = f"{PROJECT_ID}.{BIGQUERY_DATASET}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    try:
        bq.create_dataset(dataset)
        print(f"  ✓ BigQuery dataset created: {BIGQUERY_DATASET}")
    except Conflict:
        print(f"  ✓ BigQuery dataset already exists: {BIGQUERY_DATASET}")

    # Create a sample table so connect_to_bigquery_dataset has something to link
    table_id = f"{dataset_id}.{BIGQUERY_TABLE}"
    schema = [
        bigquery.SchemaField("bucket_name",  "STRING"),
        bigquery.SchemaField("event_type",   "STRING"),
        bigquery.SchemaField("object_name",  "STRING"),
        bigquery.SchemaField("event_time",   "TIMESTAMP"),
        bigquery.SchemaField("size_bytes",   "INTEGER"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    try:
        bq.create_table(table)
        print(f"  ✓ BigQuery table created: {BIGQUERY_TABLE}")
    except Conflict:
        print(f"  ✓ BigQuery table already exists: {BIGQUERY_TABLE}")

    # Insert sample rows so queries return data
    rows = [
        {"bucket_name": TEST_BUCKET_MAIN, "event_type": "OBJECT_FINALIZE",
         "object_name": "test.txt", "event_time": "2026-01-01T00:00:00Z", "size_bytes": 1024},
        {"bucket_name": TEST_BUCKET_MAIN, "event_type": "OBJECT_DELETE",
         "object_name": "old.txt", "event_time": "2026-01-02T00:00:00Z", "size_bytes": 512},
    ]
    errors = bq.insert_rows_json(table_id, rows)
    if not errors:
        print(f"  ✓ Sample rows inserted into {BIGQUERY_TABLE}")
    else:
        print(f"  ! Row insert warning: {errors}")


def create_test_files():
    TEST_FILES_DIR.mkdir(exist_ok=True)

    files = {
        "test.txt":        "Hello from GCS test suite!\nLine 2.\n",
        "document.pdf":    b"%PDF-1.4 fake pdf content for testing",
        "image.jpg":       b"\xff\xd8\xff fake jpeg content",
        "style.css":       "body { background: #000; color: #fff; }",
        "script.js":       "console.log('GCS test asset');",
        "index.html":      "<!DOCTYPE html><html><body><h1>Test Site</h1></body></html>",
        "404.html":        "<!DOCTYPE html><html><body><h1>404 Not Found</h1></body></html>",
        "large_test.bin":  b"0" * (5 * 1024 * 1024),  # 5 MB for resumable upload test
    }

    for name, content in files.items():
        path = TEST_FILES_DIR / name
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(path, mode) as f:
            f.write(content)
    print(f"  ✓ Test files created in: {TEST_FILES_DIR}")


def upload_seed_objects(gcs):
    bucket = gcs.bucket(TEST_BUCKET_MAIN)
    seed_files = ["test.txt", "document.pdf", "style.css", "script.js"]
    for fname in seed_files:
        path = TEST_FILES_DIR / fname
        if path.exists():
            blob = bucket.blob(fname)
            blob.upload_from_filename(str(path))
    print(f"  ✓ Seed objects uploaded to: {TEST_BUCKET_MAIN}")


def print_summary():
    print()
    print("=" * 60)
    print("TEST ENVIRONMENT READY")
    print("=" * 60)
    print(f"  Project:          {PROJECT_ID}")
    print(f"  Main bucket:      {TEST_BUCKET_MAIN}")
    print(f"  Backup bucket:    {TEST_BUCKET_BACKUP}")
    print(f"  Website bucket:   {TEST_BUCKET_WEBSITE}")
    print(f"  Archive bucket:   {TEST_BUCKET_ARCHIVE}")
    print(f"  BigQuery dataset: {BIGQUERY_DATASET}")
    print(f"  BigQuery table:   {BIGQUERY_TABLE}")
    print(f"  Test files dir:   {TEST_FILES_DIR}")
    print()
    print("Now run the test files in order:")
    print("  python bucket_storage_agent/tests/01_bucket_ops.py")
    print("  python bucket_storage_agent/tests/02_object_ops.py")
    print("  python bucket_storage_agent/tests/03_permissions.py")
    print("  python bucket_storage_agent/tests/04_monitoring.py")
    print("  python bucket_storage_agent/tests/05_website_hosting.py")
    print("  python bucket_storage_agent/tests/06_advanced_ops.py")
    print("  python bucket_storage_agent/tests/07_retention_holds.py")
    print("  python bucket_storage_agent/tests/08_encryption_pubsub.py")
    print("  python bucket_storage_agent/tests/09_soft_delete_batch.py")
    print("  python bucket_storage_agent/tests/10_bigquery_intelligence.py")
    print()


if __name__ == "__main__":
    print(f"\nSetting up test environment for project: {PROJECT_ID}\n")

    if not CREDS_PATH or not os.path.exists(CREDS_PATH):
        print(f"ERROR: credentials not found at: {CREDS_PATH}")
        sys.exit(1)

    gcs, bq, _ = get_clients()

    print("Creating test buckets...")
    create_bucket(gcs, TEST_BUCKET_MAIN)
    create_bucket(gcs, TEST_BUCKET_BACKUP)
    create_bucket(gcs, TEST_BUCKET_WEBSITE)
    create_bucket(gcs, TEST_BUCKET_ARCHIVE)

    print("\nCreating BigQuery dataset and table...")
    create_bigquery_dataset(bq)

    print("\nCreating local test files...")
    create_test_files()

    print("\nUploading seed objects...")
    upload_seed_objects(gcs)

    print_summary()
