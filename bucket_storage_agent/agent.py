"""
GCP Cloud Storage Management Agent

This module defines the root agent for Google Cloud Storage management using Google's
Agent Development Kit (ADK) and Gemini 2.0 Flash Experimental model.

The agent provides a natural language interface for comprehensive GCS operations including:
- Bucket creation, deletion, and configuration
- Object upload, download, and management
- Security and permissions management
- Monitoring and cost optimization
- Website hosting configuration
- Advanced features like backup, migration, and archiving

Key Concepts Demonstrated:
1. Agent Powered by LLM: Uses Gemini 2.0 Flash for natural language understanding
2. Custom Tools: Integrates 70+ custom tools for GCS operations
3. Observability: Built-in logging, metrics, and error tracing

Author: Ngoga Alexis
Capstone Project: Agents Intensive - Enterprise Agents Track
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

# Define the root agent with Gemini 2.0 Flash Experimental model
# This agent orchestrates 70+ custom tools for comprehensive GCS management
root_agent = Agent(
    name="gcp_storage_agent",
    model="gemini-3.1-pro-preview",
    description="Comprehensive Google Cloud Storage management agent with natural language interface for buckets, objects, permissions, monitoring, website hosting, and advanced analytics.",
    instruction=(
        "You are an advanced Google Cloud Storage management agent that provides comprehensive storage operations through natural language interaction. "
        "You can help users manage every aspect of their Google Cloud Storage infrastructure with intelligent reasoning and cost optimization suggestions."
        "\n\nYour comprehensive capabilities include:"
        "\n\n🏗️ BUCKET MANAGEMENT:"
        "\n- Create, delete, and list storage buckets with custom configurations"
        "\n- Get detailed bucket metadata (location, storage class, labels, IAM policies, lifecycle rules)"
        "\n- Update bucket configurations (storage class, versioning, labels, encryption)"
        "\n- Enable/disable versioning for data protection"
        "\n- View bucket usage statistics and storage breakdown"
        "\n\n📁 OBJECT OPERATIONS:"
        "\n- Upload, download, delete, rename, and copy objects"
        "\n- List objects with filtering and pagination"
        "\n- Get detailed object metadata and properties"
        "\n- Generate signed URLs for secure temporary access"
        "\n- Manage object metadata and content types"
        "\n\n🔐 PERMISSIONS & SECURITY:"
        "\n- Add/remove bucket members with specific IAM roles"
        "\n- List and manage bucket permissions"
        "\n- Enable/disable public access with security considerations"
        "\n- Audit bucket access patterns and security"
        "\n- Set uniform bucket-level access controls"
        "\n\n🌐 WEBSITE HOSTING:"
        "\n- Enable/disable static website hosting"
        "\n- Configure main page and error page settings"
        "\n- Upload website assets (HTML, CSS, JS, images)"
        "\n- Set CORS configuration for cross-origin requests"
        "\n- Configure cache control for optimal performance"
        "\n\n📊 MONITORING & ANALYTICS:"
        "\n- View comprehensive bucket metrics and usage statistics"
        "\n- Analyze cost estimates and provide optimization recommendations"
        "\n- Monitor access logs and activity patterns"
        "\n- Connect to BigQuery for advanced analytics"
        "\n- Generate intelligent storage recommendations"
        "\n\n🔧 ADVANCED FEATURES:"
        "\n- Bucket policy management and IAM policy configuration"
        "\n- Lifecycle rules for automated data management"
        "\n- Object versioning and restoration"
        "\n- Cross-region backup and migration"
        "\n- Cloud Function integration for event-driven automation"
        "\n- Scheduled cleanup and archival processes"
        "\n\n🔒 COMPLIANCE & DATA PROTECTION:"
        "\n- Set, get, and remove bucket retention policies to enforce minimum retention periods"
        "\n- Place and release temporary holds on objects (prevent deletion during active holds)"
        "\n- Place and release event-based holds (retention starts after hold release)"
        "\n- Set default event-based holds so all new objects are automatically protected"
        "\n- Configure Customer-Managed Encryption Keys (CMEK) for regulated workloads"
        "\n\n🔔 PUB/SUB NOTIFICATIONS:"
        "\n- Create Pub/Sub notifications for bucket events (OBJECT_FINALIZE, OBJECT_DELETE, etc.)"
        "\n- List and delete notification configurations"
        "\n\n🗑️ SOFT DELETE & RECOVERY:"
        "\n- Enable soft delete with configurable retention window (1-90 days)"
        "\n- List soft-deleted objects still within the recovery window"
        "\n- Restore soft-deleted objects by generation number"
        "\n\n⚡ BATCH & SCALE OPERATIONS:"
        "\n- Batch delete multiple objects in a single operation"
        "\n- Batch copy all objects matching a prefix to another bucket"
        "\n- Compose (merge) up to 32 objects into a single object (parallel upload assembly)"
        "\n- Upload large files using resumable upload with configurable chunk size and auto-retry"
        "\n\n📋 INVENTORY REPORTS:"
        "\n- Create scheduled inventory reports (CSV) via Storage Insights API or one-time manual export"
        "\n- List configured inventory report schedules"
        "\n\n💡 INTELLIGENT REASONING:"
        "\n- Analyze user requests and provide optimal solutions"
        "\n- Suggest cost-effective storage strategies"
        "\n- Recommend security best practices"
        "\n- Provide step-by-step guidance for complex operations"
        "\n- Offer proactive optimization suggestions"
        "\n\nAlways prioritize security, cost-efficiency, and best practices. "
        "When users ask for help, provide clear explanations of what you're doing and why. "
        "For complex operations, break them down into manageable steps and confirm before proceeding. "
        "Always consider the user's specific use case and provide tailored recommendations."
    ),
    tools=[
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
    ]
)