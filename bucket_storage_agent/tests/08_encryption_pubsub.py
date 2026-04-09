"""
TEST FILE 08 — CMEK Encryption & Pub/Sub Notifications (6 tools)
=================================================================
Tools tested:
  62. set_bucket_encryption
  63. get_bucket_encryption
  64. remove_bucket_encryption
  65. create_bucket_notification
  66. list_bucket_notifications
  67. delete_bucket_notification

Run: python bucket_storage_agent/tests/08_encryption_pubsub.py
Requires: FastAPI running on port 8080

IMPORTANT — Before running encryption tests:
  You need a Cloud KMS key ring and key. Create one with:
    gcloud kms keyrings create test-keyring --location=us
    gcloud kms keys create test-key --keyring=test-keyring --location=us --purpose=encryption

  Then grant the GCS service account access:
    gcloud kms keys add-iam-policy-binding test-key \
      --keyring=test-keyring --location=us \
      --member=serviceAccount:service-<PROJECT_NUMBER>@gs-project-accounts.iam.gserviceaccount.com \
      --role=roles/cloudkms.cryptoKeyEncrypterDecrypter

IMPORTANT — Before running Pub/Sub tests:
  Create a Pub/Sub topic:
    gcloud pubsub topics create gcs-notifications
  Grant GCS permission to publish:
    gsutil notification servicerequest -t gcs-notifications -f json gs://ngoga-test-main
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import run_test, TEST_BUCKET_MAIN, PROJECT_ID

# Replace PROJECT_NUMBER with your actual GCP project number (not project ID)
# Find it with: gcloud projects describe health-data-platform12345 --format='value(projectNumber)'
PROJECT_NUMBER = "YOUR_PROJECT_NUMBER"
KMS_KEY = f"projects/{PROJECT_ID}/locations/us/keyRings/test-keyring/cryptoKeys/test-key"
PUBSUB_TOPIC = f"projects/{PROJECT_ID}/topics/gcs-notifications"

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST SUITE 08: CMEK Encryption & Pub/Sub Notifications")
    print("="*60)

    # ── CMEK Encryption ────────────────────────────────────────────
    print("\n--- CMEK Encryption ---")

    # Tool 62: set_bucket_encryption
    run_test(
        "set_bucket_encryption",
        f"Set CMEK encryption on bucket '{TEST_BUCKET_MAIN}' using KMS key '{KMS_KEY}'"
    )

    # Tool 63: get_bucket_encryption
    run_test(
        "get_bucket_encryption",
        f"Show me the encryption configuration for bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 64: remove_bucket_encryption
    run_test(
        "remove_bucket_encryption",
        f"Remove the CMEK encryption from bucket '{TEST_BUCKET_MAIN}' and revert to Google-managed encryption"
    )

    # ── Pub/Sub Notifications ──────────────────────────────────────
    print("\n--- Pub/Sub Notifications ---")

    # Tool 65: create_bucket_notification
    run_test(
        "create_bucket_notification",
        f"Create a Pub/Sub notification for bucket '{TEST_BUCKET_MAIN}' to send OBJECT_FINALIZE events to topic 'gcs-notifications'"
    )

    # Tool 66: list_bucket_notifications
    run_test(
        "list_bucket_notifications",
        f"List all Pub/Sub notifications configured for bucket '{TEST_BUCKET_MAIN}'"
    )

    # Tool 67: delete_bucket_notification
    # The agent will list notifications first and then delete the one just created
    run_test(
        "delete_bucket_notification",
        f"Delete all Pub/Sub notifications from bucket '{TEST_BUCKET_MAIN}'"
    )

    print("\n✓ Suite 08 complete.\n")
