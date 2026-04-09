"""
TEST FILE 10 — BigQuery Integration & Agent Intelligence (4 tools + multi-step workflows)
==========================================================================================
Tools tested:
  78. connect_to_bigquery_dataset
  79. set_bucket_policy (lock — via lock_bucket_policy)
  80. lock_bucket_policy
  81. audit_bucket_access (full security audit workflow)

Plus multi-step intelligence tests that combine multiple tools.

Run: python bucket_storage_agent/tests/10_bigquery_intelligence.py
Requires: FastAPI running on port 8080
Prerequisites:
  - setup_test_environment.py already run (creates BigQuery dataset 'storage_analytics')
  - BigQuery API enabled in your GCP project:
      gcloud services enable bigquery.googleapis.com
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import run_test, TEST_BUCKET_MAIN, TEST_BUCKET_BACKUP, BIGQUERY_DATASET, BIGQUERY_TABLE

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST SUITE 10: BigQuery Integration & Agent Intelligence")
    print("="*60)

    # ── BigQuery Integration ───────────────────────────────────────
    print("\n--- BigQuery Integration ---")

    # Tool 78: connect_to_bigquery_dataset
    run_test(
        "connect_to_bigquery_dataset",
        f"Connect bucket '{TEST_BUCKET_MAIN}' to BigQuery dataset '{BIGQUERY_DATASET}' and table '{BIGQUERY_TABLE}'"
    )

    run_test(
        "query via BigQuery",
        f"Query the BigQuery dataset '{BIGQUERY_DATASET}' to show me all events for bucket '{TEST_BUCKET_MAIN}'"
    )

    # ── Policy Locking ─────────────────────────────────────────────
    print("\n--- Policy Locking ---")

    # Tool 79/80: lock_bucket_policy
    # NOTE: locking is IRREVERSIBLE — uses backup bucket, not main
    run_test(
        "lock_bucket_policy",
        f"Show me the retention policy for bucket '{TEST_BUCKET_BACKUP}' and explain what locking it would mean"
    )

    # ── Full Security Audit ────────────────────────────────────────
    print("\n--- Full Security Audit ---")

    # Tool 81: audit_bucket_access (comprehensive)
    run_test(
        "audit_bucket_access — full",
        f"Perform a full security audit on all my buckets: check IAM policies, public access settings, uniform bucket-level access, and identify any security risks"
    )

    # ── Multi-Step Intelligence Tests ─────────────────────────────
    print("\n--- Multi-Step Intelligence (Gemini chains multiple tools) ---")

    run_test(
        "multi-step: full website setup",
        f"Set up a complete website on bucket '{TEST_BUCKET_BACKUP}': enable hosting, set index.html as main page, set 404.html as error page, configure CORS for all origins, and give me the public URL"
    )

    run_test(
        "multi-step: cost optimization",
        f"Analyze my storage costs across all buckets, recommend the best storage class for each based on access patterns, and set up lifecycle rules to automatically archive objects older than 90 days"
    )

    run_test(
        "multi-step: backup + verify",
        f"Back up all objects from '{TEST_BUCKET_MAIN}' to '{TEST_BUCKET_BACKUP}', then verify the backup by listing both buckets and comparing object counts"
    )

    run_test(
        "multi-step: security hardening",
        f"Audit '{TEST_BUCKET_MAIN}' security, disable any public access, enable uniform bucket-level access, and summarize the final security posture"
    )

    run_test(
        "natural language: vague intent",
        "My storage costs are too high, help me understand what's going on and what I can do"
    )

    run_test(
        "natural language: problem solving",
        "I'm getting access denied errors on my bucket, what could be causing this and how do I fix it?"
    )

    print("\n✓ Suite 10 complete.\n")
    print("="*60)
    print("ALL 10 TEST SUITES COMPLETE — 81 tools exercised")
    print("="*60)
