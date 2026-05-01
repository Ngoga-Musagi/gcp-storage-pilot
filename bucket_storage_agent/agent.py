"""
GCP Cloud Storage Management Agent — Orchestrator + Specialized Sub-Agents

This module defines the multi-agent architecture for Google Cloud Storage management
using Google's Agent Development Kit (ADK). An orchestrator agent routes natural language
requests to 17 specialized sub-agents, each responsible for a specific domain of GCS
operations (bucket CRUD, object management, IAM, website hosting, monitoring, etc.).

Architecture:
    User Request → Orchestrator (root_agent) → transfer_to_agent → Sub-Agent → Tool Call → GCS API

Key Concepts:
1. Orchestrator Pattern: root_agent has no tools — it only routes via ADK's auto-injected transfer_to_agent
2. Specialized Sub-Agents: Each sub-agent has 3-6 tools scoped to a single domain
3. Description-Based Routing: The orchestrator LLM reads sub-agent descriptions to decide delegation

Author: Ngoga Alexis
"""

import os
import uuid
import json
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner

from .tools import (
    # Basic bucket operations
    create_storage_bucket,
    delete_storage_bucket,
    list_storage_buckets,

    # Bucket management
    get_bucket_details,
    update_bucket_configuration,
    enable_versioning,
    disable_versioning,
    view_bucket_usage,

    # Object operations
    upload_object,
    download_object,
    delete_object,
    rename_object,
    copy_object,
    list_objects,
    get_object_metadata,
    generate_signed_url,

    # Permissions management
    add_bucket_member,
    remove_bucket_member,
    list_bucket_permissions,
    enable_public_access,
    disable_public_access,

    # Monitoring & optimization
    view_bucket_metrics,
    view_bucket_cost_estimate,
    monitor_access_logs,

    # Website hosting
    enable_website_hosting,
    disable_website_hosting,
    set_website_main_page,
    set_website_error_page,
    upload_website_assets,
    upload_html_content,
    set_cors_configuration,
    set_cache_control,

    # Advanced features
    connect_to_bigquery_dataset,
    summarize_bucket_status,
    recommend_storage_class,

    # Bucket policy management
    get_bucket_policy,
    set_bucket_policy,
    lock_bucket_policy,
    get_bucket_iam_policy,
    set_bucket_iam_policy,
    add_bucket_label,
    remove_bucket_label,
    set_bucket_lifecycle_rules,

    # Advanced object management
    update_object_metadata,
    set_object_acl,
    get_object_acl,
    restore_object_version,

    # Advanced access & security
    audit_bucket_access,
    set_uniform_bucket_level_access,

    # Advanced monitoring
    enable_request_logging,
    disable_request_logging,
    analyze_bucket_activity,

    # Advanced operations
    sync_local_directory_to_bucket,
    backup_bucket_to_another_bucket,
    migrate_bucket_to_different_region,
    trigger_cloud_function_on_event,
    schedule_periodic_cleanup,
    archive_old_objects,

    # Retention policies
    set_retention_policy,
    get_retention_policy,
    remove_retention_policy,

    # Object holds
    set_temporary_hold,
    release_temporary_hold,
    set_event_based_hold,
    release_event_based_hold,
    set_default_event_based_hold,

    # CMEK encryption
    set_bucket_encryption,
    get_bucket_encryption,
    remove_bucket_encryption,

    # Pub/Sub notifications
    create_bucket_notification,
    list_bucket_notifications,
    delete_bucket_notification,

    # Soft delete
    enable_soft_delete,
    disable_soft_delete,
    list_soft_deleted_objects,
    restore_soft_deleted_object,

    # Batch operations
    batch_delete_objects,
    batch_copy_objects,
    compose_objects,

    # Resumable upload
    upload_large_object_resumable,

    # Inventory reports
    create_inventory_report,
    list_inventory_reports,
)


# ── Specialized Sub-Agents ─────────────────────────────────────────

MODEL = "gemini-3.1-pro-preview"

bucket_crud_agent = Agent(
    name="bucket_crud_agent",
    model=MODEL,
    description="Creates, deletes, lists, inspects, and updates GCS bucket configurations.",
    instruction=(
        "You manage bucket-level CRUD operations. You can create buckets with custom "
        "locations and storage classes, delete buckets (with optional force-delete of "
        "contents), list all buckets in the project, get detailed bucket metadata, and "
        "update bucket configurations. Always confirm destructive operations before proceeding."
    ),
    tools=[
        create_storage_bucket,
        delete_storage_bucket,
        list_storage_buckets,
        get_bucket_details,
        update_bucket_configuration,
    ],
)

bucket_config_agent = Agent(
    name="bucket_config_agent",
    model=MODEL,
    description="Configures bucket versioning, usage statistics, and labels.",
    instruction=(
        "You handle bucket configuration changes. Enable or disable object versioning, "
        "view bucket usage and storage breakdown, and manage bucket labels (add/remove). "
        "Explain the implications of each configuration change to the user."
    ),
    tools=[
        enable_versioning,
        disable_versioning,
        view_bucket_usage,
        add_bucket_label,
        remove_bucket_label,
    ],
)

object_management_agent = Agent(
    name="object_management_agent",
    model=MODEL,
    description="Uploads, downloads, deletes, renames, and lists objects in GCS buckets.",
    instruction=(
        "You handle core object operations: upload files to buckets, download files from "
        "buckets, delete objects, rename/move objects within a bucket, and list objects "
        "with filtering and pagination."
    ),
    tools=[
        upload_object,
        download_object,
        delete_object,
        rename_object,
        list_objects,
    ],
)

object_utilities_agent = Agent(
    name="object_utilities_agent",
    model=MODEL,
    description="Copies objects, manages metadata, generates signed URLs, and handles large resumable uploads.",
    instruction=(
        "You handle advanced object utilities: copy objects between buckets, get and update "
        "object metadata and custom properties, generate time-limited signed URLs for secure "
        "temporary access, and upload large files using resumable upload with chunking and "
        "auto-retry."
    ),
    tools=[
        copy_object,
        get_object_metadata,
        update_object_metadata,
        generate_signed_url,
        upload_large_object_resumable,
    ],
)

iam_permissions_agent = Agent(
    name="iam_permissions_agent",
    model=MODEL,
    description="Adds/removes bucket IAM members, lists permissions, and toggles public access.",
    instruction=(
        "You manage bucket-level IAM permissions. Add or remove members with specific IAM "
        "roles, list current permission bindings, and enable or disable public access. "
        "Always warn about security implications of granting public access and recommend "
        "least-privilege roles."
    ),
    tools=[
        add_bucket_member,
        remove_bucket_member,
        list_bucket_permissions,
        enable_public_access,
        disable_public_access,
    ],
)

security_policy_agent = Agent(
    name="security_policy_agent",
    model=MODEL,
    description="Gets/sets IAM policies, bucket security policies, and uniform bucket-level access.",
    instruction=(
        "You handle advanced security policy configuration. Get and set full IAM policies "
        "as JSON bindings, manage bucket-level security policies (public access prevention), "
        "and configure uniform bucket-level access (UBLA). Explain policy changes clearly "
        "and recommend security best practices."
    ),
    tools=[
        get_bucket_iam_policy,
        set_bucket_iam_policy,
        get_bucket_policy,
        set_bucket_policy,
        set_uniform_bucket_level_access,
    ],
)

acl_audit_agent = Agent(
    name="acl_audit_agent",
    model=MODEL,
    description="Manages per-object ACLs, audits bucket access patterns, and locks retention policies.",
    instruction=(
        "You manage object-level access control lists and audit capabilities. Set and get "
        "per-object ACLs (grant READER/WRITER/OWNER to entities), audit bucket access "
        "patterns for security reviews, and lock bucket retention policies. Warn that "
        "policy locks are irreversible."
    ),
    tools=[
        set_object_acl,
        get_object_acl,
        audit_bucket_access,
        lock_bucket_policy,
    ],
)

website_hosting_agent = Agent(
    name="website_hosting_agent",
    model=MODEL,
    description="Enables/disables static website hosting, configures index/error pages, and uploads site assets.",
    instruction=(
        "You configure GCS static website hosting. Enable or disable hosting on a bucket, "
        "set the main index page and 404 error page, and upload website asset files from "
        "a local directory with proper content types. Remind users that hosting requires "
        "public access and may need CORS configuration."
    ),
    tools=[
        enable_website_hosting,
        disable_website_hosting,
        set_website_main_page,
        set_website_error_page,
        upload_website_assets,
    ],
)

web_content_agent = Agent(
    name="web_content_agent",
    model=MODEL,
    description="Uploads HTML content, configures CORS and cache headers, and triggers Cloud Functions on bucket events.",
    instruction=(
        "You handle web content deployment and optimization. Upload HTML content directly "
        "by string (no file path needed), configure CORS policies for cross-origin requests, "
        "set cache-control headers on objects for CDN performance, and set up Cloud Function "
        "event triggers for automation on bucket events."
    ),
    tools=[
        upload_html_content,
        set_cors_configuration,
        set_cache_control,
        trigger_cloud_function_on_event,
    ],
)

monitoring_logging_agent = Agent(
    name="monitoring_logging_agent",
    model=MODEL,
    description="Views bucket metrics and cost estimates, monitors access logs, and manages request logging.",
    instruction=(
        "You handle monitoring and logging. View bucket metrics (object count, size, "
        "storage class breakdown), estimate monthly/annual costs with optimization tips, "
        "monitor recent access activity, and enable or disable request logging for audit "
        "trails."
    ),
    tools=[
        view_bucket_metrics,
        view_bucket_cost_estimate,
        monitor_access_logs,
        enable_request_logging,
        disable_request_logging,
    ],
)

analytics_agent = Agent(
    name="analytics_agent",
    model=MODEL,
    description="Analyzes bucket activity, summarizes status, recommends storage classes, and connects to BigQuery.",
    instruction=(
        "You provide analytics and intelligence. Analyze bucket activity patterns over "
        "time, generate comprehensive bucket status summaries, recommend optimal storage "
        "classes based on access frequency, and connect bucket data to BigQuery datasets "
        "for advanced analytics."
    ),
    tools=[
        analyze_bucket_activity,
        summarize_bucket_status,
        recommend_storage_class,
        connect_to_bigquery_dataset,
    ],
)

lifecycle_automation_agent = Agent(
    name="lifecycle_automation_agent",
    model=MODEL,
    description="Manages lifecycle rules, schedules cleanup, archives old objects, and creates inventory reports.",
    instruction=(
        "You manage automated lifecycle operations. Set bucket lifecycle rules for automatic "
        "storage class transitions and object deletions, schedule periodic cleanup jobs, "
        "archive objects older than a threshold to cheaper storage, and create or list "
        "inventory reports via Storage Insights."
    ),
    tools=[
        set_bucket_lifecycle_rules,
        schedule_periodic_cleanup,
        archive_old_objects,
        create_inventory_report,
        list_inventory_reports,
    ],
)

compliance_encryption_agent = Agent(
    name="compliance_encryption_agent",
    model=MODEL,
    description="Manages retention policies and customer-managed encryption keys (CMEK) for compliance.",
    instruction=(
        "You handle compliance and encryption requirements. Set, get, and remove bucket "
        "retention policies to enforce minimum data retention periods. Configure, inspect, "
        "and remove customer-managed encryption keys (CMEK) for data-at-rest encryption. "
        "Explain that locked retention policies are irreversible."
    ),
    tools=[
        set_retention_policy,
        get_retention_policy,
        remove_retention_policy,
        set_bucket_encryption,
        get_bucket_encryption,
        remove_bucket_encryption,
    ],
)

object_holds_agent = Agent(
    name="object_holds_agent",
    model=MODEL,
    description="Places and releases temporary and event-based holds on objects to prevent deletion.",
    instruction=(
        "You manage object holds for data protection. Place or release temporary holds "
        "to block object deletion during active holds. Place or release event-based holds "
        "where the retention clock starts only after the hold is released. Set default "
        "event-based holds so all new objects in a bucket are automatically protected."
    ),
    tools=[
        set_temporary_hold,
        release_temporary_hold,
        set_event_based_hold,
        release_event_based_hold,
        set_default_event_based_hold,
    ],
)

notifications_agent = Agent(
    name="notifications_agent",
    model=MODEL,
    description="Creates, lists, and deletes Pub/Sub notification configurations on buckets.",
    instruction=(
        "You manage Pub/Sub notifications for bucket events. Create notification "
        "configurations that publish to Pub/Sub topics on events like OBJECT_FINALIZE, "
        "OBJECT_DELETE, OBJECT_ARCHIVE, and OBJECT_METADATA_UPDATE. List existing "
        "notification configurations and delete notifications that are no longer needed."
    ),
    tools=[
        create_bucket_notification,
        list_bucket_notifications,
        delete_bucket_notification,
    ],
)

recovery_agent = Agent(
    name="recovery_agent",
    model=MODEL,
    description="Manages soft delete settings, lists/restores soft-deleted objects, and restores object versions.",
    instruction=(
        "You handle data recovery operations. Enable or disable soft delete with "
        "configurable retention windows (1-90 days). List soft-deleted objects still "
        "within the recovery window with their generation numbers, and restore them. "
        "Also restore previous object versions when versioning is enabled."
    ),
    tools=[
        enable_soft_delete,
        disable_soft_delete,
        list_soft_deleted_objects,
        restore_soft_deleted_object,
        restore_object_version,
    ],
)

data_transfer_agent = Agent(
    name="data_transfer_agent",
    model=MODEL,
    description="Performs batch delete/copy, composes objects, syncs directories, backs up and migrates buckets.",
    instruction=(
        "You handle bulk data operations and cross-bucket transfers. Batch delete or "
        "copy multiple objects in a single operation, compose (merge) up to 32 objects "
        "into one, sync a local directory to a bucket, backup one bucket to another, "
        "and migrate all objects to a bucket in a different region. Warn about costs "
        "and time for large-scale transfers."
    ),
    tools=[
        batch_delete_objects,
        batch_copy_objects,
        compose_objects,
        sync_local_directory_to_bucket,
        backup_bucket_to_another_bucket,
        migrate_bucket_to_different_region,
    ],
)


# ── Orchestrator (root_agent) ──────────────────────────────────────

root_agent = Agent(
    name="gcp_storage_agent",
    model=MODEL,
    description="Orchestrator for Google Cloud Storage management. Routes requests to specialized sub-agents.",
    instruction=(
        "You are the orchestrator for a comprehensive Google Cloud Storage management system. "
        "You do NOT perform storage operations yourself. Instead, you analyze each user request "
        "and route it to the most appropriate specialist agent based on its description.\n\n"
        "ROUTING RULES:\n"
        "- Read the user's request carefully and identify which domain it falls into.\n"
        "- Transfer to exactly one sub-agent per request.\n"
        "- If a request spans multiple domains (e.g., 'create a bucket and upload a file'), "
        "handle it sequentially: transfer to the first agent, then transfer to the next.\n"
        "- If the user's intent is ambiguous, ask a clarifying question before routing.\n"
        "- After a sub-agent completes, summarize the result clearly.\n\n"
        "AGENT DIRECTORY:\n"
        "- bucket_crud_agent: Create, delete, list, inspect, update buckets\n"
        "- bucket_config_agent: Versioning, labels, usage stats\n"
        "- object_management_agent: Upload, download, delete, rename, list objects\n"
        "- object_utilities_agent: Copy objects, metadata, signed URLs, resumable upload\n"
        "- iam_permissions_agent: Add/remove IAM members, list permissions, public access\n"
        "- security_policy_agent: IAM policies, bucket policies, uniform bucket-level access\n"
        "- acl_audit_agent: Object ACLs, access audit, policy lock\n"
        "- website_hosting_agent: Enable/disable hosting, page config, asset upload\n"
        "- web_content_agent: HTML upload, CORS, cache control, Cloud Function triggers\n"
        "- monitoring_logging_agent: Metrics, cost estimates, access logs, request logging\n"
        "- analytics_agent: Activity analysis, status summary, storage class recommendations, BigQuery\n"
        "- lifecycle_automation_agent: Lifecycle rules, cleanup scheduling, archival, inventory reports\n"
        "- compliance_encryption_agent: Retention policies, CMEK encryption\n"
        "- object_holds_agent: Temporary holds, event-based holds\n"
        "- notifications_agent: Pub/Sub notifications for bucket events\n"
        "- recovery_agent: Soft delete, object/version restoration\n"
        "- data_transfer_agent: Batch ops, compose, sync, backup, migrate\n\n"
        "Always prioritize security, cost-efficiency, and best practices in your guidance."
    ),
    sub_agents=[
        bucket_crud_agent,
        bucket_config_agent,
        object_management_agent,
        object_utilities_agent,
        iam_permissions_agent,
        security_policy_agent,
        acl_audit_agent,
        website_hosting_agent,
        web_content_agent,
        monitoring_logging_agent,
        analytics_agent,
        lifecycle_automation_agent,
        compliance_encryption_agent,
        object_holds_agent,
        notifications_agent,
        recovery_agent,
        data_transfer_agent,
    ],
)
