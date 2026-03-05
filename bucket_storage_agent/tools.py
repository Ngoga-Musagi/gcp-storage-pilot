
# """
# MIT License

# Copyright (c) 2024 Ngoga Alexis

# GCP Storage Management Agent using Google ADK.
# This agent handles comprehensive Google Cloud Storage operations including buckets, objects, permissions, monitoring, and website hosting.
# Part of a multi-agent system for GCP management.
# """

# import os
# import json
# import time
# from datetime import datetime, timedelta
# from typing import Dict, List, Optional, Union
# from google.adk.agents import Agent
# from google.cloud import storage
# from google.cloud import monitoring_v3
# from google.cloud import bigquery
# from google.auth import default
# from google.auth.transport.requests import Request
# from google.oauth2 import service_account
# from dotenv import load_dotenv

# # Try to import Firestore - handle gracefully if not available
# try:
#     from google.cloud import firestore
#     from google.cloud import exceptions
#     from google.cloud import firestore_admin_v1
#     from google.api_core import exceptions as api_exceptions
#     from google.api_core.exceptions import AlreadyExists, NotFound, GoogleAPICallError
#     from google.cloud.firestore_admin_v1.types import Database
#     import time
#     FIRESTORE_AVAILABLE = True
# except ImportError:
#     FIRESTORE_AVAILABLE = False
    
    
# # Load environment variables
# load_dotenv()

# def create_storage_bucket(bucket_name: str, location: str = "US", storage_class: str = "STANDARD", 
#                          versioning_enabled: bool = False):
#     """
#     Creates a Google Cloud Storage bucket with specified configuration.
    
#     Args:
#         bucket_name: Name of the bucket to create
#         location: Location for the bucket (default: US)
#         storage_class: Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
#         versioning_enabled: Enable object versioning
        
#     Returns:
#         Dictionary containing operation status and details
#     """
#     try:
#         # Get project ID
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {
#                 "status": "error",
#                 "message": "GOOGLE_CLOUD_PROJECT environment variable not set. Please check your .env file.",
#                 "resource_type": "storage_bucket"
#             }
        
#         # Check for credentials file
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path:
#             return {
#                 "status": "error",
#                 "message": "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. Please check your .env file.",
#                 "resource_type": "storage_bucket"
#             }
        
#         if not os.path.exists(creds_path):
#             return {
#                 "status": "error", 
#                 "message": f"Credentials file not found at: {creds_path}. Please check the file path.",
#                 "resource_type": "storage_bucket"
#             }
        
#         # Explicitly set the credentials
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        
#         # Get default credentials to verify they work
#         try:
#             credentials, auth_project = default()
#             if auth_project:
#                 project_id = auth_project
#         except Exception as e:
#             return {
#                 "status": "error",
#                 "message": f"Failed to authenticate with GCP: {str(e)}. Please check your credentials file.",
#                 "resource_type": "storage_bucket"
#             }
        
#         # Initialize client with explicit credentials
#         try:
#             client = storage.Client(project=project_id, credentials=credentials)
#         except Exception as e:
#             return {
#                 "status": "error",
#                 "message": f"Failed to initialize GCP client: {str(e)}",
#                 "resource_type": "storage_bucket"
#             }
        
#         # Check if bucket already exists
#         try:
#             bucket = client.get_bucket(bucket_name)
#             return {
#                 "status": "error",
#                 "message": f"Bucket '{bucket_name}' already exists",
#                 "resource_type": "storage_bucket"
#             }
#         except:
#             # Bucket doesn't exist, we can create it
#             pass
        
#         # Create the bucket with timeout handling (cross-platform)
#         import threading
        
#         def create_bucket_with_timeout():
#             try:
#                 print(f"⏳ Creating bucket '{bucket_name}' (60s timeout)...")
#                 bucket = client.create_bucket(bucket_name, location=location)
#                 bucket.storage_class = storage_class
                
#                 # Configure versioning if requested
#                 if versioning_enabled:
#                     bucket.versioning_enabled = True
                    
#                 bucket.patch()
#                 return bucket, None
#             except Exception as e:
#                 return None, e
        
#         # Use threading for timeout
#         result_container = [None]
#         error_container = [None]
        
#         def run_bucket_creation():
#             try:
#                 bucket, error = create_bucket_with_timeout()
#                 result_container[0] = bucket
#                 error_container[0] = error
#             except Exception as e:
#                 error_container[0] = e
        
#         # Start the bucket creation in a separate thread
#         creation_thread = threading.Thread(target=run_bucket_creation)
#         creation_thread.daemon = True
#         creation_thread.start()
        
#         # Wait for 60 seconds
#         creation_thread.join(timeout=60)
        
#         if creation_thread.is_alive():
#             return {
#                 "status": "error",
#                 "message": f"Bucket creation timed out after 60 seconds. This usually means the Cloud Storage API is not enabled or there are network issues.",
#                 "resource_type": "storage_bucket"
#             }
        
#         # Check results
#         if error_container[0]:
#             raise error_container[0]
        
#         bucket = result_container[0]
#         if bucket is None:
#             return {
#                 "status": "error",
#                 "message": "Unexpected error during bucket creation",
#                 "resource_type": "storage_bucket"
#             }
        
#         return {
#             "status": "success",
#             "message": f"Storage bucket '{bucket_name}' created successfully",
#             "resource_type": "storage_bucket",
#             "details": {
#                 "name": bucket.name,
#                 "location": bucket.location,
#                 "storage_class": bucket.storage_class,
#                 "versioning_enabled": bucket.versioning_enabled,
#                 "created": str(bucket.time_created) if bucket.time_created else None,
#                 "self_link": bucket.self_link
#             }
#         }
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": f"Failed to create bucket: {str(e)}. Check credentials and permissions.",
#             "resource_type": "storage_bucket"
#         }

# def delete_storage_bucket(bucket_name: str, force_delete_objects: bool = False):
#     """
#     Deletes a Google Cloud Storage bucket.
    
#     Args:
#         bucket_name: Name of the bucket to delete
#         force_delete_objects: If True, deletes all objects in the bucket first
        
#     Returns:
#         Dictionary containing operation status and details
#     """
#     try:
#         # Get project ID
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {
#                 "status": "error",
#                 "message": "GOOGLE_CLOUD_PROJECT environment variable not set",
#                 "resource_type": "storage_bucket"
#             }
        
#         # Check for credentials
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {
#                 "status": "error",
#                 "message": "GCP credentials not found. Please check your .env file.",
#                 "resource_type": "storage_bucket"
#             }
        
#         # Explicitly set the credentials
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        
#         # Get default credentials
#         try:
#             credentials, auth_project = default()
#             if auth_project:
#                 project_id = auth_project
#         except Exception as e:
#             return {
#                 "status": "error",
#                 "message": f"Failed to authenticate with GCP: {str(e)}",
#                 "resource_type": "storage_bucket"
#             }
        
#         # Initialize client with explicit credentials
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {
#                 "status": "error",
#                 "message": f"Bucket '{bucket_name}' does not exist",
#                 "resource_type": "storage_bucket"
#             }
        
#         # Check if bucket has objects
#         blobs = list(bucket.list_blobs(max_results=1))
#         if blobs and not force_delete_objects:
#             return {
#                 "status": "error",
#                 "message": f"Bucket '{bucket_name}' contains objects. Use force_delete_objects=True to delete them first",
#                 "resource_type": "storage_bucket"
#             }
        
#         # Delete all objects if force is True
#         if force_delete_objects:
#             blobs = bucket.list_blobs()
#             for blob in blobs:
#                 blob.delete()
        
#         bucket.delete()
        
#         return {
#             "status": "success",
#             "message": f"Storage bucket '{bucket_name}' deleted successfully",
#             "resource_type": "storage_bucket"
#         }
        
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": f"Failed to delete bucket: {str(e)}",
#             "resource_type": "storage_bucket"
#         }

# def list_storage_buckets():
#     """
#     Lists all storage buckets in the project.
    
#     Returns:
#         Dictionary containing list of buckets and their details
#     """
#     try:
#         # Get project ID
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {
#                 "status": "error",
#                 "message": "GOOGLE_CLOUD_PROJECT environment variable not set"
#             }
        
#         # Check for credentials
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {
#                 "status": "error",
#                 "message": "GCP credentials not found. Please check your .env file."
#             }
        
#         # Explicitly set the credentials
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        
#         # Get default credentials
#         try:
#             credentials, auth_project = default()
#             if auth_project:
#                 project_id = auth_project
#         except Exception as e:
#             return {
#                 "status": "error",
#                 "message": f"Failed to authenticate with GCP: {str(e)}"
#             }
        
#         # Initialize client with explicit credentials
#         client = storage.Client(project=project_id, credentials=credentials)
        
#         # List all buckets
#         buckets = list(client.list_buckets())
        
#         bucket_list = []
#         for bucket in buckets:
#             bucket_info = {
#                 "name": bucket.name,
#                 "location": bucket.location,
#                 "storage_class": bucket.storage_class,
#                 "versioning_enabled": bucket.versioning_enabled,
#                 "created": str(bucket.time_created) if bucket.time_created else None,
#                 "updated": str(bucket.updated) if bucket.updated else None
#             }
#             bucket_list.append(bucket_info)
        
#         return {
#             "status": "success",
#             "project_id": project_id,
#             "bucket_count": len(bucket_list),
#             "buckets": bucket_list
#         }
        
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": f"Failed to list buckets: {str(e)}"
#         }

# # ===========================================
# # BUCKET MANAGEMENT FUNCTIONS
# # ===========================================

# def get_bucket_details(bucket_name: str):
#     """
#     Retrieve comprehensive bucket metadata including location, storage class, labels, etc.
    
#     Args:
#         bucket_name: Name of the bucket to get details for
        
#     Returns:
#         Dictionary containing bucket details and metadata
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Reload bucket to get latest metadata
#         try:
#             bucket.reload()
#         except Exception as e:
#             if "not found" in str(e).lower() or "does not exist" in str(e).lower():
#                 return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
#             elif "permission" in str(e).lower() or "access" in str(e).lower():
#                 return {"status": "error", "message": f"Permission denied: Service account does not have access to bucket '{bucket_name}'. Please check IAM permissions."}
#             else:
#                 return {"status": "error", "message": f"Failed to access bucket '{bucket_name}': {str(e)}"}
        
#         # Get IAM policy
#         try:
#             policy = bucket.get_iam_policy()
#             iam_policy = {
#                 "bindings": [{"role": binding["role"], "members": list(binding["members"])} 
#                            for binding in policy.bindings]
#             }
#         except Exception as e:
#             if "permission" in str(e).lower() or "access" in str(e).lower():
#                 iam_policy = {"error": f"Permission denied: Cannot access IAM policy for bucket '{bucket_name}'. Service account needs 'storage.buckets.getIamPolicy' permission."}
#             else:
#                 iam_policy = {"error": f"Could not retrieve IAM policy: {str(e)}"}
        
#         # Get lifecycle rules
#         try:
#             lifecycle_rules = []
#             if hasattr(bucket, 'lifecycle_rules') and bucket.lifecycle_rules:
#                 for rule in bucket.lifecycle_rules:
#                     rule_dict = {
#                         "action": str(rule.action) if hasattr(rule, 'action') else None,
#                         "condition": {
#                             "age": rule.condition.age if hasattr(rule.condition, 'age') else None,
#                             "created_before": str(rule.condition.created_before) if hasattr(rule.condition, 'created_before') and rule.condition.created_before else None,
#                             "matches_storage_class": list(rule.condition.matches_storage_class) if hasattr(rule.condition, 'matches_storage_class') and rule.condition.matches_storage_class else None,
#                             "num_newer_versions": rule.condition.num_newer_versions if hasattr(rule.condition, 'num_newer_versions') else None
#                         } if hasattr(rule, 'condition') and rule.condition else None
#                     }
#                     lifecycle_rules.append(rule_dict)
#         except Exception as e:
#             lifecycle_rules = {"error": f"Could not retrieve lifecycle rules: {str(e)}"}
        
#         # Get CORS configuration
#         try:
#             cors_config = []
#             if hasattr(bucket, 'cors') and bucket.cors:
#                 for cors in bucket.cors:
#                     cors_dict = {
#                         "origin": list(cors.origin) if hasattr(cors, 'origin') and cors.origin else [],
#                         "method": list(cors.method) if hasattr(cors, 'method') and cors.method else [],
#                         "response_header": list(cors.response_header) if hasattr(cors, 'response_header') and cors.response_header else [],
#                         "max_age_seconds": cors.max_age_seconds if hasattr(cors, 'max_age_seconds') else None
#                     }
#                     cors_config.append(cors_dict)
#         except Exception as e:
#             cors_config = {"error": f"Could not retrieve CORS configuration: {str(e)}"}
        
#         return {
#             "status": "success",
#             "bucket_details": {
#                 "name": bucket.name,
#                 "location": bucket.location,
#                 "location_type": bucket.location_type,
#                 "storage_class": bucket.storage_class,
#                 "versioning_enabled": bucket.versioning_enabled,
#                 "labels": dict(bucket.labels) if bucket.labels else {},
#                 "created": str(bucket.time_created) if bucket.time_created else None,
#                 "updated": str(bucket.updated) if bucket.updated else None,
#                 "self_link": bucket.self_link,
#                 "public_access_prevention": getattr(bucket.iam_configuration, 'public_access_prevention', None) if hasattr(bucket, 'iam_configuration') and bucket.iam_configuration else None,
#                 "uniform_bucket_level_access": getattr(bucket.iam_configuration, 'uniform_bucket_level_access_enabled', None) if hasattr(bucket, 'iam_configuration') and bucket.iam_configuration else None,
#                 "default_kms_key_name": bucket.default_kms_key_name,
#                 "retention_policy": {
#                     "retention_period": getattr(bucket.retention_policy, 'retention_period', None) if hasattr(bucket, 'retention_policy') and bucket.retention_policy else None,
#                     "effective_time": str(getattr(bucket.retention_policy, 'effective_time', None)) if hasattr(bucket, 'retention_policy') and bucket.retention_policy and hasattr(bucket.retention_policy, 'effective_time') and bucket.retention_policy.effective_time else None
#                 } if hasattr(bucket, 'retention_policy') and bucket.retention_policy else None,
#                 "lifecycle_rules": lifecycle_rules,
#                 "cors_configuration": cors_config,
#                 "iam_policy": iam_policy,
#                 "website": {
#                     "main_page_suffix": getattr(bucket.website, 'main_page_suffix', None) if hasattr(bucket, 'website') and bucket.website else None,
#                     "not_found_page": getattr(bucket.website, 'not_found_page', None) if hasattr(bucket, 'website') and bucket.website else None
#                 } if hasattr(bucket, 'website') and bucket.website else None
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to get bucket details: {str(e)}"}

# def update_bucket_configuration(bucket_name: str, storage_class: Optional[str] = None, 
#                                versioning_enabled: Optional[bool] = None, labels: Optional[Dict[str, str]] = None,
#                                default_kms_key_name: Optional[str] = None):
#     """
#     Update bucket configuration including storage class, versioning, labels, etc.
    
#     Args:
#         bucket_name: Name of the bucket to update
#         storage_class: New storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
#         versioning_enabled: Enable or disable versioning
#         labels: Dictionary of labels to set
#         default_kms_key_name: Default KMS key for encryption
        
#     Returns:
#         Dictionary containing operation status and updated configuration
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Update storage class
#         if storage_class:
#             bucket.storage_class = storage_class
        
#         # Update versioning
#         if versioning_enabled is not None:
#             bucket.versioning_enabled = versioning_enabled
        
#         # Update labels
#         if labels:
#             bucket.labels = labels
        
#         # Update default KMS key
#         if default_kms_key_name:
#             bucket.default_kms_key_name = default_kms_key_name
        
#         # Apply changes
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Bucket '{bucket_name}' configuration updated successfully",
#             "updated_config": {
#                 "storage_class": bucket.storage_class,
#                 "versioning_enabled": bucket.versioning_enabled,
#                 "labels": dict(bucket.labels) if bucket.labels else {},
#                 "default_kms_key_name": bucket.default_kms_key_name
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to update bucket configuration: {str(e)}"}

# def enable_versioning(bucket_name: str):
#     """
#     Enable versioning for a bucket.
    
#     Args:
#         bucket_name: Name of the bucket to enable versioning for
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         bucket.versioning_enabled = True
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Versioning enabled for bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to enable versioning: {str(e)}"}

# def disable_versioning(bucket_name: str):
#     """
#     Disable versioning for a bucket.
    
#     Args:
#         bucket_name: Name of the bucket to disable versioning for
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         bucket.versioning_enabled = False
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Versioning disabled for bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to disable versioning: {str(e)}"}

# def view_bucket_usage(bucket_name: str):
#     """
#     Show bucket usage statistics including size, number of objects, etc.
    
#     Args:
#         bucket_name: Name of the bucket to get usage statistics for
        
#     Returns:
#         Dictionary containing bucket usage statistics
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get all blobs in the bucket
#         blobs = list(bucket.list_blobs())
        
#         total_size = 0
#         object_count = 0
#         storage_class_breakdown = {}
        
#         for blob in blobs:
#             total_size += blob.size or 0
#             object_count += 1
            
#             # Count by storage class
#             storage_class = blob.storage_class or 'STANDARD'
#             if storage_class not in storage_class_breakdown:
#                 storage_class_breakdown[storage_class] = {'count': 0, 'size': 0}
#             storage_class_breakdown[storage_class]['count'] += 1
#             storage_class_breakdown[storage_class]['size'] += blob.size or 0
        
#         # Format size in human readable format
#         def format_bytes(bytes_value):
#             for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
#                 if bytes_value < 1024.0:
#                     return f"{bytes_value:.2f} {unit}"
#                 bytes_value /= 1024.0
#             return f"{bytes_value:.2f} PB"
        
#         # Format storage class breakdown
#         formatted_breakdown = {}
#         for storage_class, data in storage_class_breakdown.items():
#             formatted_breakdown[storage_class] = {
#                 'count': data['count'],
#                 'size': format_bytes(data['size']),
#                 'size_bytes': data['size']
#             }
        
#         return {
#             "status": "success",
#             "bucket_usage": {
#                 "bucket_name": bucket_name,
#                 "total_objects": object_count,
#                 "total_size": format_bytes(total_size),
#                 "total_size_bytes": total_size,
#                 "storage_class_breakdown": formatted_breakdown,
#                 "last_updated": datetime.now().isoformat()
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to get bucket usage: {str(e)}"}

# # ===========================================
# # OBJECT OPERATIONS
# # ===========================================

# def upload_object(bucket_name: str, object_name: str, file_path: str, 
#                  content_type: Optional[str] = None, metadata: Optional[Dict[str, str]] = None):
#     """
#     Upload a file to the bucket.
    
#     Args:
#         bucket_name: Name of the bucket to upload to
#         object_name: Name/path for the object in the bucket
#         file_path: Local file path to upload
#         content_type: MIME type of the file
#         metadata: Dictionary of metadata to attach to the object
        
#     Returns:
#         Dictionary containing upload status and object details
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         if not os.path.exists(file_path):
#             return {"status": "error", "message": f"File '{file_path}' does not exist"}
        
#         blob = bucket.blob(object_name)
        
#         # Set content type if provided
#         if content_type:
#             blob.content_type = content_type
        
#         # Set metadata if provided
#         if metadata:
#             blob.metadata = metadata
        
#         # Upload the file
#         blob.upload_from_filename(file_path)
        
#         return {
#             "status": "success",
#             "message": f"File uploaded successfully as '{object_name}'",
#             "object_details": {
#                 "name": blob.name,
#                 "bucket": bucket_name,
#                 "size": blob.size,
#                 "content_type": blob.content_type,
#                 "created": str(blob.time_created) if blob.time_created else None,
#                 "updated": str(blob.updated) if blob.updated else None,
#                 "md5_hash": blob.md5_hash,
#                 "crc32c": blob.crc32c,
#                 "metadata": dict(blob.metadata) if blob.metadata else {}
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to upload object: {str(e)}"}

# def download_object(bucket_name: str, object_name: str, destination_path: str):
#     """
#     Download a file from the bucket.
    
#     Args:
#         bucket_name: Name of the bucket to download from
#         object_name: Name/path of the object in the bucket
#         destination_path: Local path where to save the downloaded file
        
#     Returns:
#         Dictionary containing download status and file details
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         blob = bucket.blob(object_name)
        
#         if not blob.exists():
#             return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
#         # Create directory if it doesn't exist
#         os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
#         # Download the file
#         blob.download_to_filename(destination_path)
        
#         return {
#             "status": "success",
#             "message": f"Object '{object_name}' downloaded successfully to '{destination_path}'",
#             "file_details": {
#                 "destination_path": destination_path,
#                 "size": blob.size,
#                 "content_type": blob.content_type,
#                 "last_modified": str(blob.updated) if blob.updated else None,
#                 "md5_hash": blob.md5_hash
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to download object: {str(e)}"}

# def delete_object(bucket_name: str, object_name: str):
#     """
#     Delete a specific file from the bucket.
    
#     Args:
#         bucket_name: Name of the bucket containing the object
#         object_name: Name/path of the object to delete
        
#     Returns:
#         Dictionary containing deletion status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         blob = bucket.blob(object_name)
        
#         if not blob.exists():
#             return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
#         blob.delete()
        
#         return {
#             "status": "success",
#             "message": f"Object '{object_name}' deleted successfully from bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to delete object: {str(e)}"}

# def rename_object(bucket_name: str, old_object_name: str, new_object_name: str):
#     """
#     Rename or move an object within a bucket.
    
#     Args:
#         bucket_name: Name of the bucket containing the object
#         old_object_name: Current name/path of the object
#         new_object_name: New name/path for the object
        
#     Returns:
#         Dictionary containing rename status and new object details
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         old_blob = bucket.blob(old_object_name)
        
#         if not old_blob.exists():
#             return {"status": "error", "message": f"Object '{old_object_name}' does not exist in bucket '{bucket_name}'"}
        
#         # Check if new object already exists
#         new_blob = bucket.blob(new_object_name)
#         if new_blob.exists():
#             return {"status": "error", "message": f"Object '{new_object_name}' already exists in bucket '{bucket_name}'"}
        
#         # Get original object properties
#         old_blob.reload()
#         original_content_type = old_blob.content_type
#         original_metadata = old_blob.metadata
#         original_cache_control = old_blob.cache_control
#         original_content_encoding = old_blob.content_encoding
#         original_content_disposition = old_blob.content_disposition
        
#         # Copy the object to new name
#         new_blob.upload_from_string(old_blob.download_as_bytes())
        
#         # Preserve all original properties
#         new_blob.content_type = original_content_type
#         if original_metadata:
#             new_blob.metadata = original_metadata
#         if original_cache_control:
#             new_blob.cache_control = original_cache_control
#         if original_content_encoding:
#             new_blob.content_encoding = original_content_encoding
#         if original_content_disposition:
#             new_blob.content_disposition = original_content_disposition
        
#         # Update the object with preserved properties
#         new_blob.patch()
        
#         # Delete the old object
#         old_blob.delete()
        
#         return {
#             "status": "success",
#             "message": f"Object renamed from '{old_object_name}' to '{new_object_name}'",
#             "new_object_details": {
#                 "name": new_blob.name,
#                 "bucket": bucket_name,
#                 "size": new_blob.size,
#                 "content_type": new_blob.content_type,
#                 "created": str(new_blob.time_created) if new_blob.time_created else None,
#                 "metadata": dict(new_blob.metadata) if new_blob.metadata else {}
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to rename object: {str(e)}"}

# def copy_object(source_bucket: str, source_object: str, destination_bucket: str, 
#                 destination_object: Optional[str] = None):
#     """
#     Copy an object between buckets.
    
#     Args:
#         source_bucket: Name of the source bucket
#         source_object: Name of the source object
#         destination_bucket: Name of the destination bucket
#         destination_object: Name for the object in destination (defaults to source_object)
        
#     Returns:
#         Dictionary containing copy status and destination object details
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
        
#         # Check source bucket and object
#         source_bucket_obj = client.bucket(source_bucket)
#         if not source_bucket_obj.exists():
#             return {"status": "error", "message": f"Source bucket '{source_bucket}' does not exist"}
        
#         source_blob = source_bucket_obj.blob(source_object)
#         if not source_blob.exists():
#             return {"status": "error", "message": f"Source object '{source_object}' does not exist in bucket '{source_bucket}'"}
        
#         # Check destination bucket
#         dest_bucket_obj = client.bucket(destination_bucket)
#         if not dest_bucket_obj.exists():
#             return {"status": "error", "message": f"Destination bucket '{destination_bucket}' does not exist"}
        
#         # Set destination object name
#         if destination_object is None:
#             destination_object = source_object
        
#         # Check if destination object already exists
#         dest_blob = dest_bucket_obj.blob(destination_object)
#         if dest_blob.exists():
#             return {"status": "error", "message": f"Destination object '{destination_object}' already exists in bucket '{destination_bucket}'"}
        
#         # Copy the object
#         source_bucket_obj.copy_blob(source_blob, dest_bucket_obj, destination_object)
        
#         # Get the copied object details
#         copied_blob = dest_bucket_obj.blob(destination_object)
#         copied_blob.reload()
        
#         return {
#             "status": "success",
#             "message": f"Object copied from '{source_bucket}/{source_object}' to '{destination_bucket}/{destination_object}'",
#             "destination_object_details": {
#                 "name": copied_blob.name,
#                 "bucket": destination_bucket,
#                 "size": copied_blob.size,
#                 "content_type": copied_blob.content_type,
#                 "created": str(copied_blob.time_created) if copied_blob.time_created else None,
#                 "metadata": dict(copied_blob.metadata) if copied_blob.metadata else {}
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to copy object: {str(e)}"}

# def list_objects(bucket_name: str, prefix: Optional[str] = None, delimiter: Optional[str] = None, max_results: Optional[int] = None):
#     """
#     List files inside a bucket.
    
#     Args:
#         bucket_name: Name of the bucket to list objects from
#         prefix: Filter objects by prefix
#         delimiter: Delimiter for grouping objects (useful for folder-like structure)
#         max_results: Maximum number of objects to return
        
#     Returns:
#         Dictionary containing list of objects and their details
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # List objects with optional parameters
#         blobs = bucket.list_blobs(prefix=prefix, delimiter=delimiter, max_results=max_results)
        
#         objects = []
#         for blob in blobs:
#             object_info = {
#                 "name": blob.name,
#                 "size": blob.size,
#                 "content_type": blob.content_type,
#                 "created": str(blob.time_created) if blob.time_created else None,
#                 "updated": str(blob.updated) if blob.updated else None,
#                 "storage_class": blob.storage_class,
#                 "md5_hash": blob.md5_hash,
#                 "crc32c": blob.crc32c,
#                 "metadata": dict(blob.metadata) if blob.metadata else {}
#             }
#             objects.append(object_info)
        
#         return {
#             "status": "success",
#             "bucket_name": bucket_name,
#             "object_count": len(objects),
#             "objects": objects,
#             "filters": {
#                 "prefix": prefix,
#                 "delimiter": delimiter,
#                 "max_results": max_results
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to list objects: {str(e)}"}

# def get_object_metadata(bucket_name: str, object_name: str):
#     """
#     Get metadata for a specific object.
    
#     Args:
#         bucket_name: Name of the bucket containing the object
#         object_name: Name/path of the object
        
#     Returns:
#         Dictionary containing object metadata
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         blob = bucket.blob(object_name)
        
#         if not blob.exists():
#             return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
#         # Reload to get latest metadata
#         blob.reload()
        
#         return {
#             "status": "success",
#             "object_metadata": {
#                 "name": blob.name,
#                 "bucket": bucket_name,
#                 "size": blob.size,
#                 "content_type": blob.content_type,
#                 "content_encoding": blob.content_encoding,
#                 "content_language": blob.content_language,
#                 "content_disposition": blob.content_disposition,
#                 "cache_control": blob.cache_control,
#                 "created": str(blob.time_created) if blob.time_created else None,
#                 "updated": str(blob.updated) if blob.updated else None,
#                 "storage_class": blob.storage_class,
#                 "md5_hash": blob.md5_hash,
#                 "crc32c": blob.crc32c,
#                 "etag": blob.etag,
#                 "generation": blob.generation,
#                 "metageneration": blob.metageneration,
#                 "metadata": dict(blob.metadata) if blob.metadata else {},
#                 "kms_key_name": blob.kms_key_name,
#                 "temporary_hold": blob.temporary_hold,
#                 "event_based_hold": blob.event_based_hold,
#                 "retention_expiration_time": str(blob.retention_expiration_time) if blob.retention_expiration_time else None,
#                 "self_link": blob.self_link,
#                 "media_link": blob.media_link,
#                 "public_url": blob.public_url
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to get object metadata: {str(e)}"}

# def generate_signed_url(bucket_name: str, object_name: str, expiration_hours: int = 1, 
#                        method: str = "GET"):
#     """
#     Generate a temporary download/upload link for an object.
    
#     Args:
#         bucket_name: Name of the bucket containing the object
#         object_name: Name/path of the object
#         expiration_hours: Number of hours until the URL expires
#         method: HTTP method (GET for download, PUT for upload)
        
#     Returns:
#         Dictionary containing the signed URL and expiration details
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         blob = bucket.blob(object_name)
        
#         # For GET requests, check if object exists
#         if method == "GET" and not blob.exists():
#             return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
#         # Generate signed URL
#         expiration_time = datetime.utcnow() + timedelta(hours=expiration_hours)
        
#         signed_url = blob.generate_signed_url(
#             expiration=expiration_time,
#             method=method,
#             version="v4"
#         )
        
#         return {
#             "status": "success",
#             "signed_url": signed_url,
#             "expiration_time": expiration_time.isoformat(),
#             "expiration_hours": expiration_hours,
#             "method": method,
#             "object_name": object_name,
#             "bucket_name": bucket_name
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to generate signed URL: {str(e)}"}

# # ===========================================
# # PERMISSIONS MANAGEMENT
# # ===========================================

# def add_bucket_member(bucket_name: str, member: str, role: str):
#     """
#     Add user/service account permissions to a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         member: Email address or service account to add (e.g., 'user@example.com', 'service-account@project.iam.gserviceaccount.com')
#         role: IAM role to assign (e.g., 'roles/storage.objectViewer', 'roles/storage.objectAdmin', 'roles/storage.admin')
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get current IAM policy
#         policy = bucket.get_iam_policy()
        
#         # Add the new binding
#         policy.bindings.append({
#             "role": role,
#             "members": {member}
#         })
        
#         # Set the updated policy
#         bucket.set_iam_policy(policy)
        
#         return {
#             "status": "success",
#             "message": f"Member '{member}' added with role '{role}' to bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to add bucket member: {str(e)}"}

# def remove_bucket_member(bucket_name: str, member: str, role: Optional[str] = None):
#     """
#     Remove user/service account permissions from a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         member: Email address or service account to remove
#         role: Specific role to remove (if None, removes from all roles)
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get current IAM policy
#         policy = bucket.get_iam_policy()
        
#         # Remove the member from bindings
#         removed_roles = []
#         for binding in policy.bindings:
#             if member in binding["members"]:
#                 if role is None or binding["role"] == role:
#                     binding["members"].discard(member)
#                     removed_roles.append(binding["role"])
        
#         # Remove empty bindings
#         policy.bindings = [binding for binding in policy.bindings if binding["members"]]
        
#         # Set the updated policy
#         bucket.set_iam_policy(policy)
        
#         return {
#             "status": "success",
#             "message": f"Member '{member}' removed from roles: {', '.join(removed_roles)} in bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to remove bucket member: {str(e)}"}

# def list_bucket_permissions(bucket_name: str):
#     """
#     List all permissions for a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
        
#     Returns:
#         Dictionary containing all bucket permissions
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get IAM policy
#         policy = bucket.get_iam_policy()
        
#         # Format permissions
#         permissions = []
#         for binding in policy.bindings:
#             permissions.append({
#                 "role": binding["role"],
#                 "members": list(binding["members"])
#             })
        
#         return {
#             "status": "success",
#             "bucket_name": bucket_name,
#             "permissions": permissions,
#             "total_bindings": len(permissions)
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to list bucket permissions: {str(e)}"}

# def enable_public_access(bucket_name: str):
#     """
#     Enable public access to a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get current IAM policy
#         policy = bucket.get_iam_policy()
        
#         # Add public access binding
#         policy.bindings.append({
#             "role": "roles/storage.objectViewer",
#             "members": {"allUsers"}
#         })
        
#         # Set the updated policy
#         bucket.set_iam_policy(policy)
        
#         return {
#             "status": "success",
#             "message": f"Public access enabled for bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to enable public access: {str(e)}"}

# def disable_public_access(bucket_name: str):
#     """
#     Disable public access to a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get current IAM policy
#         policy = bucket.get_iam_policy()
        
#         # Remove public access bindings
#         policy.bindings = [binding for binding in policy.bindings 
#                           if not ("allUsers" in binding["members"] or "allAuthenticatedUsers" in binding["members"])]
        
#         # Set the updated policy
#         bucket.set_iam_policy(policy)
        
#         return {
#             "status": "success",
#             "message": f"Public access disabled for bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to disable public access: {str(e)}"}

# # ===========================================
# # MONITORING & OPTIMIZATION
# # ===========================================

# def view_bucket_metrics(bucket_name: str, days: int = 7):
#     """
#     View bucket metrics including number of objects, total size, etc.
    
#     Args:
#         bucket_name: Name of the bucket to get metrics for
#         days: Number of days to look back for metrics
        
#     Returns:
#         Dictionary containing bucket metrics
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get all blobs in the bucket
#         blobs = list(bucket.list_blobs())
        
#         # Calculate metrics
#         total_objects = len(blobs)
#         total_size = sum(blob.size or 0 for blob in blobs)
        
#         # Group by storage class
#         storage_class_stats = {}
#         for blob in blobs:
#             storage_class = blob.storage_class or 'STANDARD'
#             if storage_class not in storage_class_stats:
#                 storage_class_stats[storage_class] = {'count': 0, 'size': 0}
#             storage_class_stats[storage_class]['count'] += 1
#             storage_class_stats[storage_class]['size'] += blob.size or 0
        
#         # Calculate average object size
#         avg_object_size = total_size / total_objects if total_objects > 0 else 0
        
#         # Format size in human readable format
#         def format_bytes(bytes_value):
#             for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
#                 if bytes_value < 1024.0:
#                     return f"{bytes_value:.2f} {unit}"
#                 bytes_value /= 1024.0
#             return f"{bytes_value:.2f} PB"
        
#         # Format storage class breakdown
#         formatted_breakdown = {}
#         for storage_class, stats in storage_class_stats.items():
#             formatted_breakdown[storage_class] = {
#                 'count': stats['count'],
#                 'size': format_bytes(stats['size']),
#                 'size_bytes': stats['size'],
#                 'percentage': (stats['size'] / total_size * 100) if total_size > 0 else 0
#             }
        
#         return {
#             "status": "success",
#             "bucket_metrics": {
#                 "bucket_name": bucket_name,
#                 "total_objects": total_objects,
#                 "total_size": format_bytes(total_size),
#                 "total_size_bytes": total_size,
#                 "average_object_size": format_bytes(avg_object_size),
#                 "average_object_size_bytes": avg_object_size,
#                 "storage_class_breakdown": formatted_breakdown,
#                 "last_updated": datetime.now().isoformat()
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to get bucket metrics: {str(e)}"}

# def view_bucket_cost_estimate(bucket_name: str):
#     """
#     View estimated costs for a bucket based on storage usage.
    
#     Args:
#         bucket_name: Name of the bucket to estimate costs for
        
#     Returns:
#         Dictionary containing cost estimates
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get all blobs in the bucket
#         blobs = list(bucket.list_blobs())
        
#         # Storage pricing (as of 2024, per GB per month)
#         storage_pricing = {
#             'STANDARD': 0.020,  # $0.020 per GB per month
#             'NEARLINE': 0.010,  # $0.010 per GB per month
#             'COLDLINE': 0.004,  # $0.004 per GB per month
#             'ARCHIVE': 0.0012   # $0.0012 per GB per month
#         }
        
#         # Calculate costs by storage class
#         total_cost = 0
#         cost_breakdown = {}
        
#         for blob in blobs:
#             storage_class = blob.storage_class or 'STANDARD'
#             size_gb = (blob.size or 0) / (1024**3)  # Convert bytes to GB
            
#             if storage_class not in cost_breakdown:
#                 cost_breakdown[storage_class] = {'size_gb': 0, 'cost': 0}
            
#             cost_breakdown[storage_class]['size_gb'] += size_gb
#             cost_breakdown[storage_class]['cost'] += size_gb * storage_pricing.get(storage_class, storage_pricing['STANDARD'])
        
#         # Calculate total cost
#         for storage_class, data in cost_breakdown.items():
#             total_cost += data['cost']
        
#         # Format cost breakdown
#         formatted_breakdown = {}
#         for storage_class, data in cost_breakdown.items():
#             formatted_breakdown[storage_class] = {
#                 'size_gb': round(data['size_gb'], 2),
#                 'monthly_cost': round(data['cost'], 4),
#                 'price_per_gb': storage_pricing.get(storage_class, storage_pricing['STANDARD'])
#             }
        
#         return {
#             "status": "success",
#             "cost_estimate": {
#                 "bucket_name": bucket_name,
#                 "total_monthly_cost": round(total_cost, 4),
#                 "total_annual_cost": round(total_cost * 12, 4),
#                 "cost_breakdown": formatted_breakdown,
#                 "currency": "USD",
#                 "pricing_note": "Based on standard Google Cloud Storage pricing (2024)",
#                 "last_updated": datetime.now().isoformat()
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to get cost estimate: {str(e)}"}

# def monitor_access_logs(bucket_name: str, hours: int = 24):
#     """
#     Monitor access logs for a bucket.
#     Note: This is a simplified implementation. For production, you'd want to use Cloud Logging.
    
#     Args:
#         bucket_name: Name of the bucket to monitor
#         hours: Number of hours to look back
        
#     Returns:
#         Dictionary containing access log information
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get bucket metadata to check recent activity
#         bucket.reload()
        
#         # Get recent objects (as a proxy for activity)
#         recent_objects = []
#         cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
#         for blob in bucket.list_blobs():
#             if blob.updated and blob.updated.replace(tzinfo=None) > cutoff_time:
#                 recent_objects.append({
#                     "name": blob.name,
#                     "size": blob.size,
#                     "updated": str(blob.updated),
#                     "storage_class": blob.storage_class
#                 })
        
#         # Sort by update time
#         recent_objects.sort(key=lambda x: x['updated'], reverse=True)
        
#         return {
#             "status": "success",
#             "access_logs": {
#                 "bucket_name": bucket_name,
#                 "monitoring_period_hours": hours,
#                 "recent_activity": {
#                     "objects_modified": len(recent_objects),
#                     "recent_objects": recent_objects[:10]  # Last 10 objects
#                 },
#                 "bucket_info": {
#                     "created": str(bucket.time_created) if bucket.time_created else None,
#                     "updated": str(bucket.updated) if bucket.updated else None,
#                     "versioning_enabled": bucket.versioning_enabled
#                 },
#                 "note": "This is a simplified access log. For detailed logging, enable Cloud Logging for your bucket.",
#                 "last_updated": datetime.now().isoformat()
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to monitor access logs: {str(e)}"}

# # ===========================================
# # WEBSITE HOSTING
# # ===========================================

# def enable_website_hosting(bucket_name: str, main_page_suffix: str = "index.html", 
#                           not_found_page: str = "404.html"):
#     """
#     Enable website hosting for a bucket.
    
#     Args:
#         bucket_name: Name of the bucket to enable website hosting for
#         main_page_suffix: Main page file (e.g., "index.html")
#         not_found_page: 404 error page file (e.g., "404.html")
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Configure website settings
#         bucket.website.main_page_suffix = main_page_suffix
#         bucket.website.not_found_page = not_found_page
        
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Website hosting enabled for bucket '{bucket_name}'",
#             "website_config": {
#                 "main_page_suffix": main_page_suffix,
#                 "not_found_page": not_found_page,
#                 "website_url": f"https://storage.googleapis.com/{bucket_name}/"
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to enable website hosting: {str(e)}"}

# def disable_website_hosting(bucket_name: str):
#     """
#     Disable website hosting for a bucket.
    
#     Args:
#         bucket_name: Name of the bucket to disable website hosting for
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Clear website settings
#         bucket.website.main_page_suffix = None
#         bucket.website.not_found_page = None
        
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Website hosting disabled for bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to disable website hosting: {str(e)}"}

# def set_website_main_page(bucket_name: str, main_page_suffix: str):
#     """
#     Set the main page for website hosting.
    
#     Args:
#         bucket_name: Name of the bucket
#         main_page_suffix: Main page file (e.g., "index.html")
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         bucket.website.main_page_suffix = main_page_suffix
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Main page set to '{main_page_suffix}' for bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to set main page: {str(e)}"}

# def set_website_error_page(bucket_name: str, not_found_page: str):
#     """
#     Set the error page for website hosting.
    
#     Args:
#         bucket_name: Name of the bucket
#         not_found_page: 404 error page file (e.g., "404.html")
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         bucket.website.not_found_page = not_found_page
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Error page set to '{not_found_page}' for bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to set error page: {str(e)}"}

# def upload_website_assets(bucket_name: str, assets_directory: str):
#     """
#     Upload website assets to a bucket.
    
#     Args:
#         bucket_name: Name of the bucket to upload assets to
#         assets_directory: Local directory containing website assets
        
#     Returns:
#         Dictionary containing upload status and asset details
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         if not os.path.exists(assets_directory):
#             return {"status": "error", "message": f"Directory '{assets_directory}' does not exist"}
        
#         uploaded_files = []
        
#         # Walk through the directory and upload files
#         for root, dirs, files in os.walk(assets_directory):
#             for file in files:
#                 local_path = os.path.join(root, file)
#                 # Create object name by removing the assets_directory prefix
#                 relative_path = os.path.relpath(local_path, assets_directory)
#                 object_name = relative_path.replace(os.sep, '/')
                
#                 blob = bucket.blob(object_name)
                
#                 # Set content type based on file extension
#                 content_type = None
#                 if file.endswith('.html'):
#                     content_type = 'text/html'
#                 elif file.endswith('.css'):
#                     content_type = 'text/css'
#                 elif file.endswith('.js'):
#                     content_type = 'application/javascript'
#                 elif file.endswith('.png'):
#                     content_type = 'image/png'
#                 elif file.endswith('.jpg') or file.endswith('.jpeg'):
#                     content_type = 'image/jpeg'
#                 elif file.endswith('.gif'):
#                     content_type = 'image/gif'
#                 elif file.endswith('.svg'):
#                     content_type = 'image/svg+xml'
                
#                 if content_type:
#                     blob.content_type = content_type
                
#                 blob.upload_from_filename(local_path)
#                 uploaded_files.append({
#                     "object_name": object_name,
#                     "size": blob.size,
#                     "content_type": blob.content_type
#                 })
        
#         return {
#             "status": "success",
#             "message": f"Uploaded {len(uploaded_files)} website assets to bucket '{bucket_name}'",
#             "uploaded_files": uploaded_files,
#             "website_url": f"https://storage.googleapis.com/{bucket_name}/"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to upload website assets: {str(e)}"}

# def set_cors_configuration(bucket_name: str, origins: List[str], methods: Optional[List[str]] = None, 
#                           headers: Optional[List[str]] = None, max_age: int = 3600):
#     """
#     Set CORS configuration for a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         origins: List of allowed origins (e.g., ['https://example.com', '*'])
#         methods: List of allowed HTTP methods (default: ['GET', 'POST', 'PUT', 'DELETE'])
#         headers: List of allowed headers (default: ['*'])
#         max_age: Maximum age for preflight requests in seconds
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Set default values
#         if methods is None:
#             methods = ['GET', 'POST', 'PUT', 'DELETE']
#         if headers is None:
#             headers = ['*']
        
#         # Configure CORS
#         cors_rule = {
#             "origin": origins,
#             "method": methods,
#             "responseHeader": headers,
#             "maxAgeSeconds": max_age
#         }
        
#         bucket.cors = [cors_rule]
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"CORS configuration set for bucket '{bucket_name}'",
#             "cors_config": cors_rule
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to set CORS configuration: {str(e)}"}

# def set_cache_control(bucket_name: str, object_name: str, cache_control: str):
#     """
#     Set cache control headers for an object.
    
#     Args:
#         bucket_name: Name of the bucket
#         object_name: Name of the object
#         cache_control: Cache control directive (e.g., "public, max-age=3600")
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         blob = bucket.blob(object_name)
        
#         if not blob.exists():
#             return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
#         blob.cache_control = cache_control
#         blob.patch()
        
#         return {
#             "status": "success",
#             "message": f"Cache control set to '{cache_control}' for object '{object_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to set cache control: {str(e)}"}

# # ===========================================
# # ADVANCED FEATURES
# # ===========================================

# def connect_to_bigquery_dataset(bucket_name: str, dataset_id: str, table_id: Optional[str] = None):
#     """
#     Connect bucket to BigQuery dataset for analytics and logging.
    
#     Args:
#         bucket_name: Name of the bucket
#         dataset_id: BigQuery dataset ID
#         table_id: Optional table ID (defaults to bucket_name)
        
#     Returns:
#         Dictionary containing connection status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         # Initialize BigQuery client
#         bq_client = bigquery.Client(project=project_id, credentials=credentials)
        
#         # Create dataset reference
#         dataset_ref = bq_client.dataset(dataset_id)
        
#         # Check if dataset exists, create if not
#         try:
#             bq_client.get_dataset(dataset_ref)
#         except Exception:
#             # Create dataset
#             dataset = bigquery.Dataset(dataset_ref)
#             dataset.location = "US"  # Default location
#             bq_client.create_dataset(dataset)
        
#         # Set table ID
#         if table_id is None:
#             table_id = bucket_name.replace('-', '_')
        
#         # Create table reference
#         table_ref = dataset_ref.table(table_id)
        
#         # Define table schema for bucket analytics
#         schema = [
#             bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
#             bigquery.SchemaField("bucket_name", "STRING", mode="REQUIRED"),
#             bigquery.SchemaField("object_name", "STRING", mode="REQUIRED"),
#             bigquery.SchemaField("operation", "STRING", mode="REQUIRED"),
#             bigquery.SchemaField("size_bytes", "INTEGER", mode="NULLABLE"),
#             bigquery.SchemaField("storage_class", "STRING", mode="NULLABLE"),
#             bigquery.SchemaField("user_agent", "STRING", mode="NULLABLE"),
#             bigquery.SchemaField("ip_address", "STRING", mode="NULLABLE")
#         ]
        
#         # Create table if it doesn't exist
#         try:
#             bq_client.get_table(table_ref)
#         except Exception:
#             table = bigquery.Table(table_ref, schema=schema)
#             bq_client.create_table(table)
        
#         return {
#             "status": "success",
#             "message": f"Bucket '{bucket_name}' connected to BigQuery dataset '{dataset_id}'",
#             "bigquery_config": {
#                 "project_id": project_id,
#                 "dataset_id": dataset_id,
#                 "table_id": table_id,
#                 "table_schema": [{"name": field.name, "type": field.field_type, "mode": field.mode} for field in schema]
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to connect to BigQuery: {str(e)}"}

# def summarize_bucket_status(bucket_name: str):
#     """
#     Summarize all key information about a bucket.
    
#     Args:
#         bucket_name: Name of the bucket to summarize
        
#     Returns:
#         Dictionary containing comprehensive bucket summary
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get comprehensive bucket information
#         bucket.reload()
        
#         # Get objects
#         blobs = list(bucket.list_blobs())
        
#         # Calculate metrics
#         total_objects = len(blobs)
#         total_size = sum(blob.size or 0 for blob in blobs)
        
#         # Storage class breakdown
#         storage_class_stats = {}
#         for blob in blobs:
#             storage_class = blob.storage_class or 'STANDARD'
#             if storage_class not in storage_class_stats:
#                 storage_class_stats[storage_class] = {'count': 0, 'size': 0}
#             storage_class_stats[storage_class]['count'] += 1
#             storage_class_stats[storage_class]['size'] += blob.size or 0
        
#         # Get IAM policy
#         try:
#             policy = bucket.get_iam_policy()
#             permissions = [{"role": binding["role"], "members": list(binding["members"])} for binding in policy.bindings]
#         except Exception:
#             permissions = []
        
#         # Format size
#         def format_bytes(bytes_value):
#             for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
#                 if bytes_value < 1024.0:
#                     return f"{bytes_value:.2f} {unit}"
#                 bytes_value /= 1024.0
#             return f"{bytes_value:.2f} PB"
        
#         # Cost estimation
#         storage_pricing = {'STANDARD': 0.020, 'NEARLINE': 0.010, 'COLDLINE': 0.004, 'ARCHIVE': 0.0012}
#         monthly_cost = 0
#         for storage_class, stats in storage_class_stats.items():
#             size_gb = stats['size'] / (1024**3)
#             monthly_cost += size_gb * storage_pricing.get(storage_class, storage_pricing['STANDARD'])
        
#         return {
#             "status": "success",
#             "bucket_summary": {
#                 "basic_info": {
#                     "name": bucket.name,
#                     "location": bucket.location,
#                     "storage_class": bucket.storage_class,
#                     "versioning_enabled": bucket.versioning_enabled,
#                     "created": str(bucket.time_created) if bucket.time_created else None,
#                     "updated": str(bucket.updated) if bucket.updated else None
#                 },
#                 "usage_stats": {
#                     "total_objects": total_objects,
#                     "total_size": format_bytes(total_size),
#                     "total_size_bytes": total_size,
#                     "average_object_size": format_bytes(total_size / total_objects) if total_objects > 0 else "0 B"
#                 },
#                 "storage_breakdown": {
#                     storage_class: {
#                         "count": stats['count'],
#                         "size": format_bytes(stats['size']),
#                         "percentage": (stats['size'] / total_size * 100) if total_size > 0 else 0
#                     } for storage_class, stats in storage_class_stats.items()
#                 },
#                 "cost_estimate": {
#                     "monthly_cost_usd": round(monthly_cost, 4),
#                     "annual_cost_usd": round(monthly_cost * 12, 4)
#                 },
#                 "permissions": {
#                     "total_bindings": len(permissions),
#                     "permissions": permissions
#                 },
#                 "website_config": {
#                     "enabled": bucket.website.main_page_suffix is not None,
#                     "main_page": bucket.website.main_page_suffix,
#                     "error_page": bucket.website.not_found_page,
#                     "url": f"https://storage.googleapis.com/{bucket_name}/" if bucket.website.main_page_suffix else None
#                 },
#                 "security": {
#                     "public_access_prevention": bucket.iam_configuration.public_access_prevention if bucket.iam_configuration else None,
#                     "uniform_bucket_level_access": bucket.iam_configuration.uniform_bucket_level_access_enabled if bucket.iam_configuration else None
#                 },
#                 "last_updated": datetime.now().isoformat()
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to summarize bucket status: {str(e)}"}

# def recommend_storage_class(bucket_name: str):
#     """
#     Suggest cost-efficient storage types based on bucket usage patterns.
    
#     Args:
#         bucket_name: Name of the bucket to analyze
        
#     Returns:
#         Dictionary containing storage class recommendations
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get all objects
#         blobs = list(bucket.list_blobs())
        
#         if not blobs:
#             return {
#                 "status": "success",
#                 "recommendations": {
#                     "message": "No objects found in bucket. No specific recommendations available.",
#                     "general_advice": "Consider using STANDARD storage class for frequently accessed data."
#                 }
#             }
        
#         # Analyze object access patterns
#         now = datetime.utcnow()
#         recent_objects = []
#         old_objects = []
        
#         for blob in blobs:
#             if blob.updated:
#                 days_since_update = (now - blob.updated.replace(tzinfo=None)).days
#                 if days_since_update <= 30:
#                     recent_objects.append(blob)
#                 else:
#                     old_objects.append(blob)
        
#         # Calculate size distribution
#         total_size = sum(blob.size or 0 for blob in blobs)
#         recent_size = sum(blob.size or 0 for blob in recent_objects)
#         old_size = sum(blob.size or 0 for blob in old_objects)
        
#         # Storage class recommendations
#         recommendations = []
        
#         # Recent data recommendation
#         if recent_objects:
#             recent_percentage = (recent_size / total_size * 100) if total_size > 0 else 0
#             if recent_percentage > 70:
#                 recommendations.append({
#                     "category": "Frequently Accessed Data",
#                     "percentage": recent_percentage,
#                     "recommendation": "STANDARD",
#                     "reasoning": "High percentage of recently updated data suggests frequent access. STANDARD class provides best performance.",
#                     "cost_impact": "Higher cost but optimal performance for active data"
#                 })
        
#         # Old data recommendations
#         if old_objects:
#             old_percentage = (old_size / total_size * 100) if total_size > 0 else 0
#             if old_percentage > 50:
#                 recommendations.append({
#                     "category": "Infrequently Accessed Data",
#                     "percentage": old_percentage,
#                     "recommendation": "NEARLINE or COLDLINE",
#                     "reasoning": "Large percentage of old data suggests infrequent access. Consider archival storage classes.",
#                     "cost_impact": "Significant cost savings (50-80% reduction) for rarely accessed data"
#                 })
        
#         # Size-based recommendations
#         large_objects = [blob for blob in blobs if (blob.size or 0) > 100 * 1024 * 1024]  # > 100MB
#         if large_objects:
#             large_size = sum(blob.size or 0 for blob in large_objects)
#             large_percentage = (large_size / total_size * 100) if total_size > 0 else 0
#             recommendations.append({
#                 "category": "Large Objects",
#                 "percentage": large_percentage,
#                 "recommendation": "Consider COLDLINE or ARCHIVE for large, infrequently accessed files",
#                 "reasoning": "Large objects that are rarely accessed can benefit from archival storage classes.",
#                 "cost_impact": "Potential 60-95% cost reduction for large archival data"
#             })
        
#         # Cost analysis
#         current_cost = 0
#         optimized_cost = 0
        
#         storage_pricing = {'STANDARD': 0.020, 'NEARLINE': 0.010, 'COLDLINE': 0.004, 'ARCHIVE': 0.0012}
        
#         for blob in blobs:
#             size_gb = (blob.size or 0) / (1024**3)
#             current_storage_class = blob.storage_class or 'STANDARD'
#             current_cost += size_gb * storage_pricing.get(current_storage_class, storage_pricing['STANDARD'])
            
#             # Optimized storage class based on age
#             if blob.updated:
#                 days_since_update = (now - blob.updated.replace(tzinfo=None)).days
#                 if days_since_update > 365:
#                     optimized_storage_class = 'ARCHIVE'
#                 elif days_since_update > 90:
#                     optimized_storage_class = 'COLDLINE'
#                 elif days_since_update > 30:
#                     optimized_storage_class = 'NEARLINE'
#                 else:
#                     optimized_storage_class = 'STANDARD'
#             else:
#                 optimized_storage_class = 'ARCHIVE'  # No update time, assume old
            
#             optimized_cost += size_gb * storage_pricing.get(optimized_storage_class, storage_pricing['STANDARD'])
        
#         savings_percentage = ((current_cost - optimized_cost) / current_cost * 100) if current_cost > 0 else 0
        
#         return {
#             "status": "success",
#             "storage_recommendations": {
#                 "bucket_name": bucket_name,
#                 "analysis_summary": {
#                     "total_objects": len(blobs),
#                     "total_size_gb": round(total_size / (1024**3), 2),
#                     "recent_objects_percentage": round((len(recent_objects) / len(blobs) * 100), 2) if blobs else 0,
#                     "old_objects_percentage": round((len(old_objects) / len(blobs) * 100), 2) if blobs else 0
#                 },
#                 "recommendations": recommendations,
#                 "cost_optimization": {
#                     "current_monthly_cost": round(current_cost, 4),
#                     "optimized_monthly_cost": round(optimized_cost, 4),
#                     "potential_savings": round(current_cost - optimized_cost, 4),
#                     "savings_percentage": round(savings_percentage, 2)
#                 },
#                 "implementation_notes": [
#                     "Review each recommendation carefully before implementing",
#                     "Consider data access patterns and business requirements",
#                     "Test with a small subset before full migration",
#                     "Monitor performance after changes"
#                 ],
#                 "last_updated": datetime.now().isoformat()
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to generate storage recommendations: {str(e)}"}

# # ===========================================
# # BUCKET POLICY MANAGEMENT
# # ===========================================

# def get_bucket_policy(bucket_name: str):
#     """
#     Get the bucket policy configuration.
    
#     Args:
#         bucket_name: Name of the bucket
        
#     Returns:
#         Dictionary containing bucket policy details
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         bucket.reload()
        
#         return {
#             "status": "success",
#             "bucket_policy": {
#                 "bucket_name": bucket_name,
#                 "public_access_prevention": bucket.iam_configuration.public_access_prevention if bucket.iam_configuration else None,
#                 "uniform_bucket_level_access": bucket.iam_configuration.uniform_bucket_level_access_enabled if bucket.iam_configuration else None,
#                 "retention_policy": {
#                     "retention_period": getattr(bucket.retention_policy, 'retention_period', None) if hasattr(bucket, 'retention_policy') and bucket.retention_policy else None,
#                     "effective_time": str(getattr(bucket.retention_policy, 'effective_time', None)) if hasattr(bucket, 'retention_policy') and bucket.retention_policy and hasattr(bucket.retention_policy, 'effective_time') and bucket.retention_policy.effective_time else None
#                 } if hasattr(bucket, 'retention_policy') and bucket.retention_policy else None,
#                 "lifecycle_rules": [],
#                 "cors_configuration": [],
#                 "labels": dict(bucket.labels) if bucket.labels else {}
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to get bucket policy: {str(e)}"}

# def set_bucket_policy(bucket_name: str, public_access_prevention: Optional[str] = None, 
#                      uniform_bucket_level_access: Optional[bool] = None):
#     """
#     Set bucket policy configuration.
    
#     Args:
#         bucket_name: Name of the bucket
#         public_access_prevention: Public access prevention setting
#         uniform_bucket_level_access: Enable/disable uniform bucket level access
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Update IAM configuration
#         if not bucket.iam_configuration:
#             bucket.iam_configuration = {}
        
#         if public_access_prevention:
#             bucket.iam_configuration.public_access_prevention = public_access_prevention
        
#         if uniform_bucket_level_access is not None:
#             bucket.iam_configuration.uniform_bucket_level_access_enabled = uniform_bucket_level_access
        
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Bucket policy updated for '{bucket_name}'",
#             "updated_policy": {
#                 "public_access_prevention": bucket.iam_configuration.public_access_prevention,
#                 "uniform_bucket_level_access": bucket.iam_configuration.uniform_bucket_level_access_enabled
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to set bucket policy: {str(e)}"}

# def lock_bucket_policy(bucket_name: str, retention_period: int):
#     """
#     Lock bucket policy with retention period.
    
#     Args:
#         bucket_name: Name of the bucket
#         retention_period: Retention period in seconds
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Set retention policy
#         bucket.retention_policy = {
#             "retention_period": retention_period,
#             "effective_time": datetime.utcnow()
#         }
        
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Bucket policy locked with {retention_period} seconds retention period",
#             "retention_policy": {
#                 "retention_period": retention_period,
#                 "effective_time": datetime.utcnow().isoformat()
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to lock bucket policy: {str(e)}"}

# def get_bucket_iam_policy(bucket_name: str):
#     """
#     Get bucket IAM policy.
    
#     Args:
#         bucket_name: Name of the bucket
        
#     Returns:
#         Dictionary containing IAM policy
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         policy = bucket.get_iam_policy()
        
#         return {
#             "status": "success",
#             "iam_policy": {
#                 "bucket_name": bucket_name,
#                 "bindings": [{"role": binding["role"], "members": list(binding["members"])} for binding in policy.bindings],
#                 "etag": policy.etag
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to get bucket IAM policy: {str(e)}"}

# def set_bucket_iam_policy(bucket_name: str, bindings: str):
#     """
#     Set bucket IAM policy.
    
#     Args:
#         bucket_name: Name of the bucket
#         bindings: JSON string containing list of IAM bindings with role and members
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Parse bindings from JSON string
#         try:
#             bindings_list = json.loads(bindings)
#         except json.JSONDecodeError:
#             return {"status": "error", "message": "Invalid JSON format for bindings parameter"}
        
#         # Create new policy
#         policy = bucket.get_iam_policy()
#         policy.bindings = bindings_list
        
#         bucket.set_iam_policy(policy)
        
#         return {
#             "status": "success",
#             "message": f"IAM policy updated for bucket '{bucket_name}'",
#             "updated_bindings": bindings
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to set bucket IAM policy: {str(e)}"}

# def add_bucket_label(bucket_name: str, key: str, value: str):
#     """
#     Add a label to a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         key: Label key
#         value: Label value
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Add label
#         if not bucket.labels:
#             bucket.labels = {}
#         bucket.labels[key] = value
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Label '{key}: {value}' added to bucket '{bucket_name}'",
#             "labels": dict(bucket.labels)
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to add bucket label: {str(e)}"}

# def remove_bucket_label(bucket_name: str, key: str):
#     """
#     Remove a label from a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         key: Label key to remove
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Remove label
#         if bucket.labels and key in bucket.labels:
#             del bucket.labels[key]
#             bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Label '{key}' removed from bucket '{bucket_name}'",
#             "labels": dict(bucket.labels) if bucket.labels else {}
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to remove bucket label: {str(e)}"}

# def set_bucket_lifecycle_rules(bucket_name: str, rules: str):
#     """
#     Set lifecycle rules for a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         rules: JSON string containing list of lifecycle rules
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Parse rules from JSON string
#         try:
#             rules_list = json.loads(rules)
#         except json.JSONDecodeError:
#             return {"status": "error", "message": "Invalid JSON format for rules parameter"}
        
#         # Set lifecycle rules
#         bucket.lifecycle_rules = rules_list
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Lifecycle rules set for bucket '{bucket_name}'",
#             "rules": rules
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to set bucket lifecycle rules: {str(e)}"}

# # ===========================================
# # ADVANCED OBJECT MANAGEMENT
# # ===========================================

# def update_object_metadata(bucket_name: str, object_name: str, metadata: Dict[str, str]):
#     """
#     Update metadata for an object.
    
#     Args:
#         bucket_name: Name of the bucket
#         object_name: Name of the object
#         metadata: Dictionary of metadata to update
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         blob = bucket.blob(object_name)
        
#         if not blob.exists():
#             return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
#         # Update metadata
#         blob.metadata = metadata
#         blob.patch()
        
#         return {
#             "status": "success",
#             "message": f"Metadata updated for object '{object_name}'",
#             "updated_metadata": metadata
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to update object metadata: {str(e)}"}

# def set_object_acl(bucket_name: str, object_name: str, entity: str, role: str):
#     """
#     Set ACL (Access Control List) for an object.
    
#     Args:
#         bucket_name: Name of the bucket
#         object_name: Name of the object
#         entity: Entity to grant access to (e.g., 'allUsers', 'allAuthenticatedUsers', 'user@example.com')
#         role: Role to grant (e.g., 'READER', 'WRITER', 'OWNER')
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         blob = bucket.blob(object_name)
        
#         if not blob.exists():
#             return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
#         # Set ACL
#         blob.acl.entity(entity).grant(role)
#         blob.acl.save()
        
#         return {
#             "status": "success",
#             "message": f"ACL set for object '{object_name}': {entity} -> {role}",
#             "acl_entry": {"entity": entity, "role": role}
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to set object ACL: {str(e)}"}

# def get_object_acl(bucket_name: str, object_name: str):
#     """
#     Get ACL (Access Control List) for an object.
    
#     Args:
#         bucket_name: Name of the bucket
#         object_name: Name of the object
        
#     Returns:
#         Dictionary containing object ACL
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         blob = bucket.blob(object_name)
        
#         if not blob.exists():
#             return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
#         # Reload blob to get latest information
#         try:
#             blob.reload()
#         except Exception as e:
#             if "permission" in str(e).lower() or "access" in str(e).lower():
#                 return {"status": "error", "message": f"Permission denied: Cannot access object '{object_name}'. Service account needs 'storage.objects.get' permission."}
#             else:
#                 return {"status": "error", "message": f"Failed to access object '{object_name}': {str(e)}"}
        
#         # Get ACL
#         acl_entries = []
#         try:
#             for entry in blob.acl:
#                 acl_entries.append({
#                     "entity": str(entry.entity) if hasattr(entry, 'entity') else None,
#                     "role": str(entry.role) if hasattr(entry, 'role') else None
#                 })
#         except Exception as acl_error:
#             return {
#                 "status": "error", 
#                 "message": f"Failed to retrieve ACL entries: {str(acl_error)}. This might be due to insufficient permissions or the object not having ACL configured."
#             }
        
#         return {
#             "status": "success",
#             "object_acl": {
#                 "bucket_name": bucket_name,
#                 "object_name": object_name,
#                 "acl_entries": acl_entries
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to get object ACL: {str(e)}"}

# def restore_object_version(bucket_name: str, object_name: str, generation: Optional[str] = None):
#     """
#     Restore a specific version of an object.
    
#     Args:
#         bucket_name: Name of the bucket
#         object_name: Name of the object
#         generation: Specific generation to restore (if None, restores latest)
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Check if versioning is enabled
#         if not bucket.versioning_enabled:
#             return {"status": "error", "message": f"Versioning is not enabled for bucket '{bucket_name}'"}
        
#         # List object versions
#         versions = list(bucket.list_blobs(prefix=object_name, versions=True))
#         object_versions = [v for v in versions if v.name == object_name]
        
#         if not object_versions:
#             return {"status": "error", "message": f"No versions found for object '{object_name}'"}
        
#         # Sort by generation (newest first)
#         object_versions.sort(key=lambda x: x.generation, reverse=True)
        
#         if generation:
#             # Find specific version
#             target_version = None
#             for version in object_versions:
#                 if str(version.generation) == str(generation):
#                     target_version = version
#                     break
            
#             if not target_version:
#                 return {"status": "error", "message": f"Version {generation} not found for object '{object_name}'"}
#         else:
#             # Use the latest version
#             target_version = object_versions[0]
        
#         # Copy the version to create a new current version
#         new_blob = bucket.blob(object_name)
#         new_blob.upload_from_string(target_version.download_as_bytes())
        
#         # Copy metadata if it exists
#         if target_version.metadata:
#             new_blob.metadata = target_version.metadata
#             new_blob.patch()
        
#         return {
#             "status": "success",
#             "message": f"Object '{object_name}' restored from version {target_version.generation}",
#             "restored_version": {
#                 "generation": target_version.generation,
#                 "created": str(target_version.time_created) if target_version.time_created else None,
#                 "size": target_version.size
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to restore object version: {str(e)}"}

# # ===========================================
# # ADVANCED ACCESS & SECURITY
# # ===========================================

# def audit_bucket_access(bucket_name: str, days: int = 7):
#     """
#     Audit bucket access patterns and permissions.
    
#     Args:
#         bucket_name: Name of the bucket
#         days: Number of days to analyze
        
#     Returns:
#         Dictionary containing access audit results
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Get bucket IAM policy
#         try:
#             policy = bucket.get_iam_policy()
#             iam_bindings = [{"role": binding["role"], "members": list(binding["members"])} for binding in policy.bindings]
#         except Exception:
#             iam_bindings = []
        
#         # Get recent objects as proxy for activity
#         cutoff_time = datetime.utcnow() - timedelta(days=days)
#         recent_objects = []
        
#         for blob in bucket.list_blobs():
#             if blob.updated and blob.updated.replace(tzinfo=None) > cutoff_time:
#                 recent_objects.append({
#                     "name": blob.name,
#                     "size": blob.size,
#                     "updated": str(blob.updated),
#                     "storage_class": blob.storage_class
#                 })
        
#         # Analyze access patterns
#         total_objects = len(list(bucket.list_blobs()))
#         recent_count = len(recent_objects)
#         activity_percentage = (recent_count / total_objects * 100) if total_objects > 0 else 0
        
#         # Security analysis
#         public_access = False
#         for binding in iam_bindings:
#             if "allUsers" in binding["members"] or "allAuthenticatedUsers" in binding["members"]:
#                 public_access = True
#                 break
        
#         return {
#             "status": "success",
#             "access_audit": {
#                 "bucket_name": bucket_name,
#                 "analysis_period_days": days,
#                 "total_objects": total_objects,
#                 "recent_activity": {
#                     "objects_modified": recent_count,
#                     "activity_percentage": round(activity_percentage, 2),
#                     "recent_objects": recent_objects[:10]  # Last 10 objects
#                 },
#                 "security_analysis": {
#                     "public_access": public_access,
#                     "iam_bindings_count": len(iam_bindings),
#                     "uniform_bucket_level_access": bucket.iam_configuration.uniform_bucket_level_access_enabled if bucket.iam_configuration else None,
#                     "public_access_prevention": bucket.iam_configuration.public_access_prevention if bucket.iam_configuration else None
#                 },
#                 "recommendations": [
#                     "Review IAM bindings regularly" if len(iam_bindings) > 10 else None,
#                     "Consider enabling uniform bucket level access" if not bucket.iam_configuration.uniform_bucket_level_access_enabled else None,
#                     "Monitor for unusual access patterns" if activity_percentage > 50 else None
#                 ],
#                 "last_updated": datetime.now().isoformat()
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to audit bucket access: {str(e)}"}

# def set_uniform_bucket_level_access(bucket_name: str, enabled: bool):
#     """
#     Set uniform bucket level access for a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         enabled: Enable or disable uniform bucket level access
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Set uniform bucket level access
#         if not bucket.iam_configuration:
#             bucket.iam_configuration = {}
        
#         bucket.iam_configuration.uniform_bucket_level_access_enabled = enabled
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Uniform bucket level access {'enabled' if enabled else 'disabled'} for bucket '{bucket_name}'",
#             "uniform_bucket_level_access": enabled
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to set uniform bucket level access: {str(e)}"}

# # ===========================================
# # ADVANCED MONITORING
# # ===========================================

# def enable_request_logging(bucket_name: str, log_bucket: Optional[str] = None):
#     """
#     Enable request logging for a bucket.
    
#     Args:
#         bucket_name: Name of the bucket to enable logging for
#         log_bucket: Bucket to store logs in (defaults to same bucket)
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Set log bucket
#         if log_bucket:
#             log_bucket_obj = client.bucket(log_bucket)
#             if not log_bucket_obj.exists():
#                 return {"status": "error", "message": f"Log bucket '{log_bucket}' does not exist"}
#             bucket.logging.log_bucket = log_bucket
#         else:
#             bucket.logging.log_bucket = bucket_name
        
#         # Set log object prefix
#         bucket.logging.log_object_prefix = f"access-logs/{bucket_name}/"
        
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Request logging enabled for bucket '{bucket_name}'",
#             "logging_config": {
#                 "log_bucket": bucket.logging.log_bucket,
#                 "log_object_prefix": bucket.logging.log_object_prefix
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to enable request logging: {str(e)}"}

# def disable_request_logging(bucket_name: str):
#     """
#     Disable request logging for a bucket.
    
#     Args:
#         bucket_name: Name of the bucket to disable logging for
        
#     Returns:
#         Dictionary containing operation status
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Clear logging configuration
#         bucket.logging.log_bucket = None
#         bucket.logging.log_object_prefix = None
        
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Request logging disabled for bucket '{bucket_name}'"
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to disable request logging: {str(e)}"}

# def analyze_bucket_activity(bucket_name: str, days: int = 30):
#     """
#     Analyze bucket activity patterns and provide insights.
    
#     Args:
#         bucket_name: Name of the bucket to analyze
#         days: Number of days to analyze
        
#     Returns:
#         Dictionary containing activity analysis
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Analyze objects by creation/update time
#         cutoff_time = datetime.utcnow() - timedelta(days=days)
        
#         # Get all objects
#         all_objects = list(bucket.list_blobs())
        
#         # Categorize objects by activity
#         recent_count = 0
#         old_count = 0
#         large_count = 0
#         small_count = 0
        
#         total_size = 0
#         storage_class_distribution = {}
        
#         for blob in all_objects:
#             total_size += blob.size or 0
            
#             # Categorize by age
#             if blob.updated and blob.updated.replace(tzinfo=None) > cutoff_time:
#                 recent_count += 1
#             else:
#                 old_count += 1
            
#             # Categorize by size
#             if (blob.size or 0) > 100 * 1024 * 1024:  # > 100MB
#                 large_count += 1
#             else:
#                 small_count += 1
            
#             # Count by storage class
#             storage_class = blob.storage_class or 'STANDARD'
#             storage_class_distribution[storage_class] = storage_class_distribution.get(storage_class, 0) + 1
        
#         # Calculate metrics
#         total_objects = len(all_objects)
        
#         # Activity patterns
#         activity_percentage = (recent_count / total_objects * 100) if total_objects > 0 else 0
#         large_object_percentage = (large_count / total_objects * 100) if total_objects > 0 else 0
        
#         # Storage efficiency analysis
#         def format_bytes(bytes_value):
#             for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
#                 if bytes_value < 1024.0:
#                     return f"{bytes_value:.2f} {unit}"
#                 bytes_value /= 1024.0
#             return f"{bytes_value:.2f} PB"
        
#         # Generate insights
#         insights = []
#         recommendations = []
        
#         if activity_percentage < 10:
#             insights.append("Low activity bucket - most objects are not recently accessed")
#             recommendations.append("Consider moving old objects to cheaper storage classes")
        
#         if large_object_percentage > 20:
#             insights.append("High percentage of large objects")
#             recommendations.append("Consider compression or chunking for large files")
        
#         if storage_class_distribution.get('STANDARD', 0) / total_objects > 0.8:
#             insights.append("Most objects are in STANDARD storage class")
#             recommendations.append("Review storage class distribution for cost optimization")
        
#         return {
#             "status": "success",
#             "activity_analysis": {
#                 "bucket_name": bucket_name,
#                 "analysis_period_days": days,
#                 "summary": {
#                     "total_objects": total_objects,
#                     "total_size": format_bytes(total_size),
#                     "total_size_bytes": total_size,
#                     "average_object_size": format_bytes(total_size / total_objects) if total_objects > 0 else "0 B"
#                 },
#                 "activity_patterns": {
#                     "recent_objects": recent_count,
#                     "old_objects": old_count,
#                     "activity_percentage": round(activity_percentage, 2),
#                     "large_objects": large_count,
#                     "small_objects": small_count,
#                     "large_object_percentage": round(large_object_percentage, 2)
#                 },
#                 "storage_distribution": storage_class_distribution,
#                 "insights": insights,
#                 "recommendations": recommendations,
#                 "last_updated": datetime.now().isoformat()
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to analyze bucket activity: {str(e)}"}

# # ===========================================
# # ADVANCED OPERATIONS
# # ===========================================

# def sync_local_directory_to_bucket(bucket_name: str, local_directory: str, 
#                                  destination_prefix: str = "", exclude_patterns: Optional[List[str]] = None):
#     """
#     Sync a local directory to a bucket.
    
#     Args:
#         bucket_name: Name of the bucket
#         local_directory: Local directory to sync
#         destination_prefix: Prefix for objects in bucket
#         exclude_patterns: List of patterns to exclude
        
#     Returns:
#         Dictionary containing sync results
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         if not os.path.exists(local_directory):
#             return {"status": "error", "message": f"Local directory '{local_directory}' does not exist"}
        
#         uploaded_files = []
#         skipped_files = []
        
#         # Walk through directory
#         for root, dirs, files in os.walk(local_directory):
#             for file in files:
#                 local_path = os.path.join(root, file)
                
#                 # Check exclude patterns
#                 should_exclude = False
#                 if exclude_patterns:
#                     for pattern in exclude_patterns:
#                         if pattern in local_path:
#                             should_exclude = True
#                             break
                
#                 if should_exclude:
#                     skipped_files.append(local_path)
#                     continue
                
#                 # Create object name
#                 relative_path = os.path.relpath(local_path, local_directory)
#                 object_name = f"{destination_prefix}{relative_path}".replace(os.sep, '/')
                
#                 # Upload file
#                 blob = bucket.blob(object_name)
                
#                 # Set content type based on extension
#                 content_type = None
#                 if file.endswith('.html'):
#                     content_type = 'text/html'
#                 elif file.endswith('.css'):
#                     content_type = 'text/css'
#                 elif file.endswith('.js'):
#                     content_type = 'application/javascript'
#                 elif file.endswith('.json'):
#                     content_type = 'application/json'
#                 elif file.endswith('.png'):
#                     content_type = 'image/png'
#                 elif file.endswith('.jpg') or file.endswith('.jpeg'):
#                     content_type = 'image/jpeg'
                
#                 if content_type:
#                     blob.content_type = content_type
                
#                 blob.upload_from_filename(local_path)
#                 uploaded_files.append({
#                     "local_path": local_path,
#                     "object_name": object_name,
#                     "size": blob.size,
#                     "content_type": blob.content_type
#                 })
        
#         return {
#             "status": "success",
#             "message": f"Synced {len(uploaded_files)} files to bucket '{bucket_name}'",
#             "sync_results": {
#                 "uploaded_files": uploaded_files,
#                 "skipped_files": skipped_files,
#                 "total_uploaded": len(uploaded_files),
#                 "total_skipped": len(skipped_files)
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to sync directory: {str(e)}"}

# def backup_bucket_to_another_bucket(source_bucket: str, destination_bucket: str, 
#                                    destination_prefix: str = ""):
#     """
#     Backup a bucket to another bucket.
    
#     Args:
#         source_bucket: Name of the source bucket
#         destination_bucket: Name of the destination bucket
#         destination_prefix: Prefix for objects in destination bucket
        
#     Returns:
#         Dictionary containing backup results
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
        
#         # Check source bucket
#         source_bucket_obj = client.bucket(source_bucket)
#         if not source_bucket_obj.exists():
#             return {"status": "error", "message": f"Source bucket '{source_bucket}' does not exist"}
        
#         # Check destination bucket
#         dest_bucket_obj = client.bucket(destination_bucket)
#         if not dest_bucket_obj.exists():
#             return {"status": "error", "message": f"Destination bucket '{destination_bucket}' does not exist"}
        
#         # Copy objects
#         copied_objects = []
#         failed_objects = []
        
#         for blob in source_bucket_obj.list_blobs():
#             try:
#                 # Create destination object name
#                 dest_object_name = f"{destination_prefix}{blob.name}"
                
#                 # Copy object
#                 source_bucket_obj.copy_blob(blob, dest_bucket_obj, dest_object_name)
                
#                 copied_objects.append({
#                     "source_name": blob.name,
#                     "destination_name": dest_object_name,
#                     "size": blob.size
#                 })
#             except Exception as e:
#                 failed_objects.append({
#                     "object_name": blob.name,
#                     "error": str(e)
#                 })
        
#         return {
#             "status": "success",
#             "message": f"Backup completed: {len(copied_objects)} objects copied",
#             "backup_results": {
#                 "copied_objects": copied_objects,
#                 "failed_objects": failed_objects,
#                 "total_copied": len(copied_objects),
#                 "total_failed": len(failed_objects)
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to backup bucket: {str(e)}"}

# def migrate_bucket_to_different_region(source_bucket: str, destination_bucket: str, 
#                                      destination_region: str):
#     """
#     Migrate a bucket to a different region.
    
#     Args:
#         source_bucket: Name of the source bucket
#         destination_bucket: Name of the destination bucket
#         destination_region: Target region for migration
        
#     Returns:
#         Dictionary containing migration results
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
        
#         # Check source bucket
#         source_bucket_obj = client.bucket(source_bucket)
#         if not source_bucket_obj.exists():
#             return {"status": "error", "message": f"Source bucket '{source_bucket}' does not exist"}
        
#         # Create destination bucket in new region
#         dest_bucket_obj = client.bucket(destination_bucket)
#         if not dest_bucket_obj.exists():
#             dest_bucket_obj = client.create_bucket(destination_bucket, location=destination_region)
        
#         # Copy all objects
#         migrated_objects = []
#         failed_objects = []
        
#         for blob in source_bucket_obj.list_blobs():
#             try:
#                 # Copy object to destination bucket
#                 source_bucket_obj.copy_blob(blob, dest_bucket_obj, blob.name)
#                 migrated_objects.append({
#                     "object_name": blob.name,
#                     "size": blob.size
#                 })
#             except Exception as e:
#                 failed_objects.append({
#                     "object_name": blob.name,
#                     "error": str(e)
#                 })
        
#         return {
#             "status": "success",
#             "message": f"Migration completed: {len(migrated_objects)} objects migrated to {destination_region}",
#             "migration_results": {
#                 "migrated_objects": migrated_objects,
#                 "failed_objects": failed_objects,
#                 "total_migrated": len(migrated_objects),
#                 "total_failed": len(failed_objects),
#                 "destination_region": destination_region
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to migrate bucket: {str(e)}"}

# def archive_old_objects(bucket_name: str, days_old: int = 365, 
#                        target_storage_class: str = "ARCHIVE"):
#     """
#     Archive old objects to a different storage class.
    
#     Args:
#         bucket_name: Name of the bucket
#         days_old: Age threshold in days
#         target_storage_class: Target storage class for archiving
        
#     Returns:
#         Dictionary containing archiving results
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Find old objects
#         cutoff_time = datetime.utcnow() - timedelta(days=days_old)
#         old_objects = []
        
#         for blob in bucket.list_blobs():
#             if blob.updated and blob.updated.replace(tzinfo=None) < cutoff_time:
#                 old_objects.append(blob)
        
#         # Archive objects
#         archived_objects = []
#         failed_objects = []
        
#         for blob in old_objects:
#             try:
#                 # Create new blob with different storage class
#                 new_blob = bucket.blob(blob.name)
#                 new_blob.upload_from_string(blob.download_as_bytes())
#                 new_blob.storage_class = target_storage_class
#                 new_blob.patch()
                
#                 # Delete old blob
#                 blob.delete()
                
#                 archived_objects.append({
#                     "object_name": blob.name,
#                     "size": blob.size,
#                     "new_storage_class": target_storage_class
#                 })
#             except Exception as e:
#                 failed_objects.append({
#                     "object_name": blob.name,
#                     "error": str(e)
#                 })
        
#         return {
#             "status": "success",
#             "message": f"Archived {len(archived_objects)} objects to {target_storage_class} storage class",
#             "archiving_results": {
#                 "archived_objects": archived_objects,
#                 "failed_objects": failed_objects,
#                 "total_archived": len(archived_objects),
#                 "total_failed": len(failed_objects),
#                 "target_storage_class": target_storage_class
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to archive old objects: {str(e)}"}

# def schedule_periodic_cleanup(bucket_name: str, cleanup_rules: str):
#     """
#     Schedule periodic cleanup based on rules.
    
#     Args:
#         bucket_name: Name of the bucket
#         cleanup_rules: JSON string containing list of cleanup rules
        
#     Returns:
#         Dictionary containing cleanup schedule
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Parse cleanup rules from JSON string
#         try:
#             cleanup_rules_list = json.loads(cleanup_rules)
#         except json.JSONDecodeError:
#             return {"status": "error", "message": "Invalid JSON format for cleanup_rules parameter"}
        
#         # Set lifecycle rules for cleanup
#         bucket.lifecycle_rules = cleanup_rules_list
#         bucket.patch()
        
#         return {
#             "status": "success",
#             "message": f"Periodic cleanup scheduled for bucket '{bucket_name}'",
#             "cleanup_schedule": {
#                 "bucket_name": bucket_name,
#                 "rules": cleanup_rules,
#                 "scheduled_at": datetime.now().isoformat()
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to schedule periodic cleanup: {str(e)}"}

# def trigger_cloud_function_on_event(bucket_name: str, function_name: str, 
#                                    event_type: str = "finalize"):
#     """
#     Configure bucket to trigger cloud function on events.
    
#     Args:
#         bucket_name: Name of the bucket
#         function_name: Name of the cloud function
#         event_type: Type of event to trigger on
        
#     Returns:
#         Dictionary containing trigger configuration
#     """
#     try:
#         project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
#         if not project_id:
#             return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
#         creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#         if not creds_path or not os.path.exists(creds_path):
#             return {"status": "error", "message": "GCP credentials not found"}
        
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
#         credentials, auth_project = default()
#         if auth_project:
#             project_id = auth_project
        
#         client = storage.Client(project=project_id, credentials=credentials)
#         bucket = client.bucket(bucket_name)
        
#         if not bucket.exists():
#             return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
#         # Note: This is a simplified implementation
#         # In practice, you would use Cloud Functions API to set up the trigger
        
#         return {
#             "status": "success",
#             "message": f"Cloud function trigger configured for bucket '{bucket_name}'",
#             "trigger_config": {
#                 "bucket_name": bucket_name,
#                 "function_name": function_name,
#                 "event_type": event_type,
#                 "note": "This is a simplified implementation. Use Cloud Functions API for full configuration."
#             }
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"Failed to configure cloud function trigger: {str(e)}"}

"""
MIT License

Copyright (c) 2024 Ngoga Alexis

GCP Storage Management Agent using Google ADK.
This agent handles comprehensive Google Cloud Storage operations including buckets, objects, permissions, monitoring, and website hosting.
Part of a multi-agent system for GCP management.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from google.adk.agents import Agent
from google.cloud import storage
from google.cloud import monitoring_v3
from google.cloud import bigquery
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from dotenv import load_dotenv

# Try to import Firestore - handle gracefully if not available
try:
    from google.cloud import firestore
    from google.cloud import exceptions
    from google.cloud import firestore_admin_v1
    from google.api_core import exceptions as api_exceptions
    from google.api_core.exceptions import AlreadyExists, NotFound, GoogleAPICallError
    from google.cloud.firestore_admin_v1.types import Database
    import time
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    
    
# Load environment variables
load_dotenv()

def create_storage_bucket(bucket_name: str, location: str = "US", storage_class: str = "STANDARD", 
                         versioning_enabled: bool = False):
    """
    Creates a Google Cloud Storage bucket with specified configuration.
    
    Args:
        bucket_name: Name of the bucket to create
        location: Location for the bucket (default: US)
        storage_class: Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
        versioning_enabled: Enable object versioning
        
    Returns:
        Dictionary containing operation status and details
    """
    try:
        # Get project ID
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {
                "status": "error",
                "message": "GOOGLE_CLOUD_PROJECT environment variable not set. Please check your .env file.",
                "resource_type": "storage_bucket"
            }
        
        # Check for credentials file
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            return {
                "status": "error",
                "message": "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. Please check your .env file.",
                "resource_type": "storage_bucket"
            }
        
        if not os.path.exists(creds_path):
            return {
                "status": "error", 
                "message": f"Credentials file not found at: {creds_path}. Please check the file path.",
                "resource_type": "storage_bucket"
            }
        
        # Explicitly set the credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        
        # Get default credentials to verify they work
        try:
            credentials, auth_project = default()
            if auth_project:
                project_id = auth_project
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to authenticate with GCP: {str(e)}. Please check your credentials file.",
                "resource_type": "storage_bucket"
            }
        
        # Initialize client with explicit credentials
        try:
            client = storage.Client(project=project_id, credentials=credentials)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to initialize GCP client: {str(e)}",
                "resource_type": "storage_bucket"
            }
        
        # Check if bucket already exists
        try:
            bucket = client.get_bucket(bucket_name)
            return {
                "status": "error",
                "message": f"Bucket '{bucket_name}' already exists",
                "resource_type": "storage_bucket"
            }
        except:
            # Bucket doesn't exist, we can create it
            pass
        
        # Create the bucket with timeout handling (cross-platform)
        import threading
        
        def create_bucket_with_timeout():
            try:
                print(f"⏳ Creating bucket '{bucket_name}' (60s timeout)...")
                bucket = client.create_bucket(bucket_name, location=location)
                bucket.storage_class = storage_class
                
                # Configure versioning if requested
                if versioning_enabled:
                    bucket.versioning_enabled = True
                    
                bucket.patch()
                return bucket, None
            except Exception as e:
                return None, e
        
        # Use threading for timeout
        result_container = [None]
        error_container = [None]
        
        def run_bucket_creation():
            try:
                bucket, error = create_bucket_with_timeout()
                result_container[0] = bucket
                error_container[0] = error
            except Exception as e:
                error_container[0] = e
        
        # Start the bucket creation in a separate thread
        creation_thread = threading.Thread(target=run_bucket_creation)
        creation_thread.daemon = True
        creation_thread.start()
        
        # Wait for 60 seconds
        creation_thread.join(timeout=60)
        
        if creation_thread.is_alive():
            return {
                "status": "error",
                "message": f"Bucket creation timed out after 60 seconds. This usually means the Cloud Storage API is not enabled or there are network issues.",
                "resource_type": "storage_bucket"
            }
        
        # Check results
        if error_container[0]:
            raise error_container[0]
        
        bucket = result_container[0]
        if bucket is None:
            return {
                "status": "error",
                "message": "Unexpected error during bucket creation",
                "resource_type": "storage_bucket"
            }
        
        return {
            "status": "success",
            "message": f"Storage bucket '{bucket_name}' created successfully",
            "resource_type": "storage_bucket",
            "details": {
                "name": bucket.name,
                "location": bucket.location,
                "storage_class": bucket.storage_class,
                "versioning_enabled": bucket.versioning_enabled,
                "created": str(bucket.time_created) if bucket.time_created else None,
                "self_link": bucket.self_link
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create bucket: {str(e)}. Check credentials and permissions.",
            "resource_type": "storage_bucket"
        }

def delete_storage_bucket(bucket_name: str, force_delete_objects: bool = False):
    """
    Deletes a Google Cloud Storage bucket.
    
    Args:
        bucket_name: Name of the bucket to delete
        force_delete_objects: If True, deletes all objects in the bucket first
        
    Returns:
        Dictionary containing operation status and details
    """
    try:
        # Get project ID
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {
                "status": "error",
                "message": "GOOGLE_CLOUD_PROJECT environment variable not set",
                "resource_type": "storage_bucket"
            }
        
        # Check for credentials
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {
                "status": "error",
                "message": "GCP credentials not found. Please check your .env file.",
                "resource_type": "storage_bucket"
            }
        
        # Explicitly set the credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        
        # Get default credentials
        try:
            credentials, auth_project = default()
            if auth_project:
                project_id = auth_project
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to authenticate with GCP: {str(e)}",
                "resource_type": "storage_bucket"
            }
        
        # Initialize client with explicit credentials
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {
                "status": "error",
                "message": f"Bucket '{bucket_name}' does not exist",
                "resource_type": "storage_bucket"
            }
        
        # Check if bucket has objects
        blobs = list(bucket.list_blobs(max_results=1))
        if blobs and not force_delete_objects:
            return {
                "status": "error",
                "message": f"Bucket '{bucket_name}' contains objects. Use force_delete_objects=True to delete them first",
                "resource_type": "storage_bucket"
            }
        
        # Delete all objects if force is True
        if force_delete_objects:
            blobs = bucket.list_blobs()
            for blob in blobs:
                blob.delete()
        
        bucket.delete()
        
        return {
            "status": "success",
            "message": f"Storage bucket '{bucket_name}' deleted successfully",
            "resource_type": "storage_bucket"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to delete bucket: {str(e)}",
            "resource_type": "storage_bucket"
        }

def list_storage_buckets():
    """
    Lists all storage buckets in the project.
    
    Returns:
        Dictionary containing list of buckets and their details
    """
    try:
        # Get project ID
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {
                "status": "error",
                "message": "GOOGLE_CLOUD_PROJECT environment variable not set"
            }
        
        # Check for credentials
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {
                "status": "error",
                "message": "GCP credentials not found. Please check your .env file."
            }
        
        # Explicitly set the credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        
        # Get default credentials
        try:
            credentials, auth_project = default()
            if auth_project:
                project_id = auth_project
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to authenticate with GCP: {str(e)}"
            }
        
        # Initialize client with explicit credentials
        client = storage.Client(project=project_id, credentials=credentials)
        
        # List all buckets
        buckets = list(client.list_buckets())
        
        bucket_list = []
        for bucket in buckets:
            bucket_info = {
                "name": bucket.name,
                "location": bucket.location,
                "storage_class": bucket.storage_class,
                "versioning_enabled": bucket.versioning_enabled,
                "created": str(bucket.time_created) if bucket.time_created else None,
                "updated": str(bucket.updated) if bucket.updated else None
            }
            bucket_list.append(bucket_info)
        
        return {
            "status": "success",
            "project_id": project_id,
            "bucket_count": len(bucket_list),
            "buckets": bucket_list
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to list buckets: {str(e)}"
        }

# ===========================================
# BUCKET MANAGEMENT FUNCTIONS
# ===========================================

def get_bucket_details(bucket_name: str):
    """
    Retrieve comprehensive bucket metadata including location, storage class, labels, etc.
    
    Args:
        bucket_name: Name of the bucket to get details for
        
    Returns:
        Dictionary containing bucket details and metadata
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Reload bucket to get latest metadata
        try:
            bucket.reload()
        except Exception as e:
            if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
            elif "permission" in str(e).lower() or "access" in str(e).lower():
                return {"status": "error", "message": f"Permission denied: Service account does not have access to bucket '{bucket_name}'. Please check IAM permissions."}
            else:
                return {"status": "error", "message": f"Failed to access bucket '{bucket_name}': {str(e)}"}
        
        # Get IAM policy
        try:
            policy = bucket.get_iam_policy()
            iam_policy = {
                "bindings": [{"role": binding["role"], "members": list(binding["members"])} 
                           for binding in policy.bindings]
            }
        except Exception as e:
            if "permission" in str(e).lower() or "access" in str(e).lower():
                iam_policy = {"error": f"Permission denied: Cannot access IAM policy for bucket '{bucket_name}'. Service account needs 'storage.buckets.getIamPolicy' permission."}
            else:
                iam_policy = {"error": f"Could not retrieve IAM policy: {str(e)}"}
        
        # Get lifecycle rules
        try:
            lifecycle_rules = []
            if hasattr(bucket, 'lifecycle_rules') and bucket.lifecycle_rules:
                for rule in bucket.lifecycle_rules:
                    rule_dict = {
                        "action": str(rule.action) if hasattr(rule, 'action') else None,
                        "condition": {
                            "age": rule.condition.age if hasattr(rule.condition, 'age') else None,
                            "created_before": str(rule.condition.created_before) if hasattr(rule.condition, 'created_before') and rule.condition.created_before else None,
                            "matches_storage_class": list(rule.condition.matches_storage_class) if hasattr(rule.condition, 'matches_storage_class') and rule.condition.matches_storage_class else None,
                            "num_newer_versions": rule.condition.num_newer_versions if hasattr(rule.condition, 'num_newer_versions') else None
                        } if hasattr(rule, 'condition') and rule.condition else None
                    }
                    lifecycle_rules.append(rule_dict)
        except Exception as e:
            lifecycle_rules = {"error": f"Could not retrieve lifecycle rules: {str(e)}"}
        
        # Get CORS configuration
        try:
            cors_config = []
            if hasattr(bucket, 'cors') and bucket.cors:
                for cors in bucket.cors:
                    cors_dict = {
                        "origin": list(cors.origin) if hasattr(cors, 'origin') and cors.origin else [],
                        "method": list(cors.method) if hasattr(cors, 'method') and cors.method else [],
                        "response_header": list(cors.response_header) if hasattr(cors, 'response_header') and cors.response_header else [],
                        "max_age_seconds": cors.max_age_seconds if hasattr(cors, 'max_age_seconds') else None
                    }
                    cors_config.append(cors_dict)
        except Exception as e:
            cors_config = {"error": f"Could not retrieve CORS configuration: {str(e)}"}
        
        return {
            "status": "success",
            "bucket_details": {
                "name": bucket.name,
                "location": bucket.location,
                "location_type": bucket.location_type,
                "storage_class": bucket.storage_class,
                "versioning_enabled": bucket.versioning_enabled,
                "labels": dict(bucket.labels) if bucket.labels else {},
                "created": str(bucket.time_created) if bucket.time_created else None,
                "updated": str(bucket.updated) if bucket.updated else None,
                "self_link": bucket.self_link,
                "public_access_prevention": getattr(bucket.iam_configuration, 'public_access_prevention', None) if hasattr(bucket, 'iam_configuration') and bucket.iam_configuration else None,
                "uniform_bucket_level_access": getattr(bucket.iam_configuration, 'uniform_bucket_level_access_enabled', None) if hasattr(bucket, 'iam_configuration') and bucket.iam_configuration else None,
                "default_kms_key_name": bucket.default_kms_key_name,
                "retention_policy": {
                    "retention_period": getattr(bucket.retention_policy, 'retention_period', None) if hasattr(bucket, 'retention_policy') and bucket.retention_policy else None,
                    "effective_time": str(getattr(bucket.retention_policy, 'effective_time', None)) if hasattr(bucket, 'retention_policy') and bucket.retention_policy and hasattr(bucket.retention_policy, 'effective_time') and bucket.retention_policy.effective_time else None
                } if hasattr(bucket, 'retention_policy') and bucket.retention_policy else None,
                "lifecycle_rules": lifecycle_rules,
                "cors_configuration": cors_config,
                "iam_policy": iam_policy,
                "website": {
                    "main_page_suffix": getattr(bucket.website, 'main_page_suffix', None) if hasattr(bucket, 'website') and bucket.website else None,
                    "not_found_page": getattr(bucket.website, 'not_found_page', None) if hasattr(bucket, 'website') and bucket.website else None
                } if hasattr(bucket, 'website') and bucket.website else None
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get bucket details: {str(e)}"}

def update_bucket_configuration(bucket_name: str, storage_class: Optional[str] = None, 
                               versioning_enabled: Optional[bool] = None, labels: Optional[Dict[str, str]] = None,
                               default_kms_key_name: Optional[str] = None):
    """
    Update bucket configuration including storage class, versioning, labels, etc.
    
    Args:
        bucket_name: Name of the bucket to update
        storage_class: New storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
        versioning_enabled: Enable or disable versioning
        labels: Dictionary of labels to set
        default_kms_key_name: Default KMS key for encryption
        
    Returns:
        Dictionary containing operation status and updated configuration
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Update storage class
        if storage_class:
            bucket.storage_class = storage_class
        
        # Update versioning
        if versioning_enabled is not None:
            bucket.versioning_enabled = versioning_enabled
        
        # Update labels
        if labels:
            bucket.labels = labels
        
        # Update default KMS key
        if default_kms_key_name:
            bucket.default_kms_key_name = default_kms_key_name
        
        # Apply changes
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Bucket '{bucket_name}' configuration updated successfully",
            "updated_config": {
                "storage_class": bucket.storage_class,
                "versioning_enabled": bucket.versioning_enabled,
                "labels": dict(bucket.labels) if bucket.labels else {},
                "default_kms_key_name": bucket.default_kms_key_name
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to update bucket configuration: {str(e)}"}

def enable_versioning(bucket_name: str):
    """
    Enable versioning for a bucket.
    
    Args:
        bucket_name: Name of the bucket to enable versioning for
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        bucket.versioning_enabled = True
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Versioning enabled for bucket '{bucket_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to enable versioning: {str(e)}"}

def disable_versioning(bucket_name: str):
    """
    Disable versioning for a bucket.
    
    Args:
        bucket_name: Name of the bucket to disable versioning for
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        bucket.versioning_enabled = False
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Versioning disabled for bucket '{bucket_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to disable versioning: {str(e)}"}

def view_bucket_usage(bucket_name: str):
    """
    Show bucket usage statistics including size, number of objects, etc.
    
    Args:
        bucket_name: Name of the bucket to get usage statistics for
        
    Returns:
        Dictionary containing bucket usage statistics
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get all blobs in the bucket
        blobs = list(bucket.list_blobs())
        
        total_size = 0
        object_count = 0
        storage_class_breakdown = {}
        
        for blob in blobs:
            total_size += blob.size or 0
            object_count += 1
            
            # Count by storage class
            storage_class = blob.storage_class or 'STANDARD'
            if storage_class not in storage_class_breakdown:
                storage_class_breakdown[storage_class] = {'count': 0, 'size': 0}
            storage_class_breakdown[storage_class]['count'] += 1
            storage_class_breakdown[storage_class]['size'] += blob.size or 0
        
        # Format size in human readable format
        def format_bytes(bytes_value):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.2f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.2f} PB"
        
        # Format storage class breakdown
        formatted_breakdown = {}
        for storage_class, data in storage_class_breakdown.items():
            formatted_breakdown[storage_class] = {
                'count': data['count'],
                'size': format_bytes(data['size']),
                'size_bytes': data['size']
            }
        
        return {
            "status": "success",
            "bucket_usage": {
                "bucket_name": bucket_name,
                "total_objects": object_count,
                "total_size": format_bytes(total_size),
                "total_size_bytes": total_size,
                "storage_class_breakdown": formatted_breakdown,
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get bucket usage: {str(e)}"}

# ===========================================
# OBJECT OPERATIONS
# ===========================================

def upload_object(bucket_name: str, object_name: str, file_path: str, 
                 content_type: Optional[str] = None, metadata: Optional[Dict[str, str]] = None):
    """
    Upload a file to the bucket.
    
    Args:
        bucket_name: Name of the bucket to upload to
        object_name: Name/path for the object in the bucket
        file_path: Local file path to upload
        content_type: MIME type of the file
        metadata: Dictionary of metadata to attach to the object
        
    Returns:
        Dictionary containing upload status and object details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File '{file_path}' does not exist"}
        
        blob = bucket.blob(object_name)
        
        # Set content type if provided
        if content_type:
            blob.content_type = content_type
        
        # Set metadata if provided
        if metadata:
            blob.metadata = metadata
        
        # Upload the file
        blob.upload_from_filename(file_path)
        
        return {
            "status": "success",
            "message": f"File uploaded successfully as '{object_name}'",
            "object_details": {
                "name": blob.name,
                "bucket": bucket_name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": str(blob.time_created) if blob.time_created else None,
                "updated": str(blob.updated) if blob.updated else None,
                "md5_hash": blob.md5_hash,
                "crc32c": blob.crc32c,
                "metadata": dict(blob.metadata) if blob.metadata else {}
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to upload object: {str(e)}"}

def download_object(bucket_name: str, object_name: str, destination_path: str):
    """
    Download a file from the bucket.
    
    Args:
        bucket_name: Name of the bucket to download from
        object_name: Name/path of the object in the bucket
        destination_path: Local path where to save the downloaded file
        
    Returns:
        Dictionary containing download status and file details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        blob = bucket.blob(object_name)
        
        if not blob.exists():
            return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Download the file
        blob.download_to_filename(destination_path)
        
        return {
            "status": "success",
            "message": f"Object '{object_name}' downloaded successfully to '{destination_path}'",
            "file_details": {
                "destination_path": destination_path,
                "size": blob.size,
                "content_type": blob.content_type,
                "last_modified": str(blob.updated) if blob.updated else None,
                "md5_hash": blob.md5_hash
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to download object: {str(e)}"}

def delete_object(bucket_name: str, object_name: str):
    """
    Delete a specific file from the bucket.
    
    Args:
        bucket_name: Name of the bucket containing the object
        object_name: Name/path of the object to delete
        
    Returns:
        Dictionary containing deletion status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        blob = bucket.blob(object_name)
        
        if not blob.exists():
            return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
        blob.delete()
        
        return {
            "status": "success",
            "message": f"Object '{object_name}' deleted successfully from bucket '{bucket_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete object: {str(e)}"}

def rename_object(bucket_name: str, old_object_name: str, new_object_name: str):
    """
    Rename or move an object within a bucket.
    
    Args:
        bucket_name: Name of the bucket containing the object
        old_object_name: Current name/path of the object
        new_object_name: New name/path for the object
        
    Returns:
        Dictionary containing rename status and new object details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        old_blob = bucket.blob(old_object_name)
        
        if not old_blob.exists():
            return {"status": "error", "message": f"Object '{old_object_name}' does not exist in bucket '{bucket_name}'"}
        
        # Check if new object already exists
        new_blob = bucket.blob(new_object_name)
        if new_blob.exists():
            return {"status": "error", "message": f"Object '{new_object_name}' already exists in bucket '{bucket_name}'"}
        
        # Get original object properties
        old_blob.reload()
        original_content_type = old_blob.content_type
        original_metadata = old_blob.metadata
        original_cache_control = old_blob.cache_control
        original_content_encoding = old_blob.content_encoding
        original_content_disposition = old_blob.content_disposition
        
        # Copy the object to new name
        new_blob.upload_from_string(old_blob.download_as_bytes())
        
        # Preserve all original properties
        new_blob.content_type = original_content_type
        if original_metadata:
            new_blob.metadata = original_metadata
        if original_cache_control:
            new_blob.cache_control = original_cache_control
        if original_content_encoding:
            new_blob.content_encoding = original_content_encoding
        if original_content_disposition:
            new_blob.content_disposition = original_content_disposition
        
        # Update the object with preserved properties
        new_blob.patch()
        
        # Delete the old object
        old_blob.delete()
        
        return {
            "status": "success",
            "message": f"Object renamed from '{old_object_name}' to '{new_object_name}'",
            "new_object_details": {
                "name": new_blob.name,
                "bucket": bucket_name,
                "size": new_blob.size,
                "content_type": new_blob.content_type,
                "created": str(new_blob.time_created) if new_blob.time_created else None,
                "metadata": dict(new_blob.metadata) if new_blob.metadata else {}
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to rename object: {str(e)}"}

def copy_object(source_bucket: str, source_object: str, destination_bucket: str, 
                destination_object: Optional[str] = None):
    """
    Copy an object between buckets.
    
    Args:
        source_bucket: Name of the source bucket
        source_object: Name of the source object
        destination_bucket: Name of the destination bucket
        destination_object: Name for the object in destination (defaults to source_object)
        
    Returns:
        Dictionary containing copy status and destination object details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        
        # Check source bucket and object
        source_bucket_obj = client.bucket(source_bucket)
        if not source_bucket_obj.exists():
            return {"status": "error", "message": f"Source bucket '{source_bucket}' does not exist"}
        
        source_blob = source_bucket_obj.blob(source_object)
        if not source_blob.exists():
            return {"status": "error", "message": f"Source object '{source_object}' does not exist in bucket '{source_bucket}'"}
        
        # Check destination bucket
        dest_bucket_obj = client.bucket(destination_bucket)
        if not dest_bucket_obj.exists():
            return {"status": "error", "message": f"Destination bucket '{destination_bucket}' does not exist"}
        
        # Set destination object name
        if destination_object is None:
            destination_object = source_object
        
        # Check if destination object already exists
        dest_blob = dest_bucket_obj.blob(destination_object)
        if dest_blob.exists():
            return {"status": "error", "message": f"Destination object '{destination_object}' already exists in bucket '{destination_bucket}'"}
        
        # Copy the object
        source_bucket_obj.copy_blob(source_blob, dest_bucket_obj, destination_object)
        
        # Get the copied object details
        copied_blob = dest_bucket_obj.blob(destination_object)
        copied_blob.reload()
        
        return {
            "status": "success",
            "message": f"Object copied from '{source_bucket}/{source_object}' to '{destination_bucket}/{destination_object}'",
            "destination_object_details": {
                "name": copied_blob.name,
                "bucket": destination_bucket,
                "size": copied_blob.size,
                "content_type": copied_blob.content_type,
                "created": str(copied_blob.time_created) if copied_blob.time_created else None,
                "metadata": dict(copied_blob.metadata) if copied_blob.metadata else {}
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to copy object: {str(e)}"}

def list_objects(bucket_name: str, prefix: Optional[str] = None, delimiter: Optional[str] = None, max_results: Optional[int] = None):
    """
    List files inside a bucket.
    
    Args:
        bucket_name: Name of the bucket to list objects from
        prefix: Filter objects by prefix
        delimiter: Delimiter for grouping objects (useful for folder-like structure)
        max_results: Maximum number of objects to return
        
    Returns:
        Dictionary containing list of objects and their details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # List objects with optional parameters
        blobs = bucket.list_blobs(prefix=prefix, delimiter=delimiter, max_results=max_results)
        
        objects = []
        for blob in blobs:
            object_info = {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": str(blob.time_created) if blob.time_created else None,
                "updated": str(blob.updated) if blob.updated else None,
                "storage_class": blob.storage_class,
                "md5_hash": blob.md5_hash,
                "crc32c": blob.crc32c,
                "metadata": dict(blob.metadata) if blob.metadata else {}
            }
            objects.append(object_info)
        
        return {
            "status": "success",
            "bucket_name": bucket_name,
            "object_count": len(objects),
            "objects": objects,
            "filters": {
                "prefix": prefix,
                "delimiter": delimiter,
                "max_results": max_results
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list objects: {str(e)}"}

def get_object_metadata(bucket_name: str, object_name: str):
    """
    Get metadata for a specific object.
    
    Args:
        bucket_name: Name of the bucket containing the object
        object_name: Name/path of the object
        
    Returns:
        Dictionary containing object metadata
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        blob = bucket.blob(object_name)
        
        if not blob.exists():
            return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
        # Reload to get latest metadata
        blob.reload()
        
        return {
            "status": "success",
            "object_metadata": {
                "name": blob.name,
                "bucket": bucket_name,
                "size": blob.size,
                "content_type": blob.content_type,
                "content_encoding": blob.content_encoding,
                "content_language": blob.content_language,
                "content_disposition": blob.content_disposition,
                "cache_control": blob.cache_control,
                "created": str(blob.time_created) if blob.time_created else None,
                "updated": str(blob.updated) if blob.updated else None,
                "storage_class": blob.storage_class,
                "md5_hash": blob.md5_hash,
                "crc32c": blob.crc32c,
                "etag": blob.etag,
                "generation": blob.generation,
                "metageneration": blob.metageneration,
                "metadata": dict(blob.metadata) if blob.metadata else {},
                "kms_key_name": blob.kms_key_name,
                "temporary_hold": blob.temporary_hold,
                "event_based_hold": blob.event_based_hold,
                "retention_expiration_time": str(blob.retention_expiration_time) if blob.retention_expiration_time else None,
                "self_link": blob.self_link,
                "media_link": blob.media_link,
                "public_url": blob.public_url
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get object metadata: {str(e)}"}

def generate_signed_url(bucket_name: str, object_name: str, expiration_hours: int = 1, 
                       method: str = "GET"):
    """
    Generate a temporary download/upload link for an object.
    
    Args:
        bucket_name: Name of the bucket containing the object
        object_name: Name/path of the object
        expiration_hours: Number of hours until the URL expires
        method: HTTP method (GET for download, PUT for upload)
        
    Returns:
        Dictionary containing the signed URL and expiration details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        blob = bucket.blob(object_name)
        
        # For GET requests, check if object exists
        if method == "GET" and not blob.exists():
            return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
        # Generate signed URL
        expiration_time = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        signed_url = blob.generate_signed_url(
            expiration=expiration_time,
            method=method,
            version="v4"
        )
        
        return {
            "status": "success",
            "signed_url": signed_url,
            "expiration_time": expiration_time.isoformat(),
            "expiration_hours": expiration_hours,
            "method": method,
            "object_name": object_name,
            "bucket_name": bucket_name
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to generate signed URL: {str(e)}"}

# ===========================================
# PERMISSIONS MANAGEMENT
# ===========================================

def add_bucket_member(bucket_name: str, member: str, role: str):
    """
    Add user/service account permissions to a bucket.
    
    Args:
        bucket_name: Name of the bucket
        member: Email address or service account to add (e.g., 'user@example.com', 'service-account@project.iam.gserviceaccount.com')
        role: IAM role to assign (e.g., 'roles/storage.objectViewer', 'roles/storage.objectAdmin', 'roles/storage.admin')
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get current IAM policy
        policy = bucket.get_iam_policy()
        
        # Add the new binding
        policy.bindings.append({
            "role": role,
            "members": {member}
        })
        
        # Set the updated policy
        bucket.set_iam_policy(policy)
        
        return {
            "status": "success",
            "message": f"Member '{member}' added with role '{role}' to bucket '{bucket_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to add bucket member: {str(e)}"}

def remove_bucket_member(bucket_name: str, member: str, role: Optional[str] = None):
    """
    Remove user/service account permissions from a bucket.
    
    Args:
        bucket_name: Name of the bucket
        member: Email address or service account to remove
        role: Specific role to remove (if None, removes from all roles)
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get current IAM policy
        policy = bucket.get_iam_policy()
        
        # Remove the member from bindings
        removed_roles = []
        for binding in policy.bindings:
            if member in binding["members"]:
                if role is None or binding["role"] == role:
                    binding["members"].discard(member)
                    removed_roles.append(binding["role"])
        
        # Remove empty bindings
        policy.bindings = [binding for binding in policy.bindings if binding["members"]]
        
        # Set the updated policy
        bucket.set_iam_policy(policy)
        
        return {
            "status": "success",
            "message": f"Member '{member}' removed from roles: {', '.join(removed_roles)} in bucket '{bucket_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to remove bucket member: {str(e)}"}

def list_bucket_permissions(bucket_name: str):
    """
    List all permissions for a bucket.
    
    Args:
        bucket_name: Name of the bucket
        
    Returns:
        Dictionary containing all bucket permissions
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get IAM policy
        policy = bucket.get_iam_policy()
        
        # Format permissions
        permissions = []
        for binding in policy.bindings:
            permissions.append({
                "role": binding["role"],
                "members": list(binding["members"])
            })
        
        return {
            "status": "success",
            "bucket_name": bucket_name,
            "permissions": permissions,
            "total_bindings": len(permissions)
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list bucket permissions: {str(e)}"}

def enable_public_access(bucket_name: str):
    """
    Enable public access to a bucket.
    
    Args:
        bucket_name: Name of the bucket
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get current IAM policy
        policy = bucket.get_iam_policy()
        
        # Add public access binding
        policy.bindings.append({
            "role": "roles/storage.objectViewer",
            "members": {"allUsers"}
        })
        
        # Set the updated policy
        bucket.set_iam_policy(policy)
        
        return {
            "status": "success",
            "message": f"Public access enabled for bucket '{bucket_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to enable public access: {str(e)}"}

def disable_public_access(bucket_name: str):
    """
    Disable public access to a bucket.
    
    Args:
        bucket_name: Name of the bucket
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get current IAM policy
        policy = bucket.get_iam_policy()
        
        # Remove public access bindings
        policy.bindings = [binding for binding in policy.bindings 
                          if not ("allUsers" in binding["members"] or "allAuthenticatedUsers" in binding["members"])]
        
        # Set the updated policy
        bucket.set_iam_policy(policy)
        
        return {
            "status": "success",
            "message": f"Public access disabled for bucket '{bucket_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to disable public access: {str(e)}"}

# ===========================================
# MONITORING & OPTIMIZATION
# ===========================================

def view_bucket_metrics(bucket_name: str, days: int = 7):
    """
    View bucket metrics including number of objects, total size, etc.
    
    Args:
        bucket_name: Name of the bucket to get metrics for
        days: Number of days to look back for metrics
        
    Returns:
        Dictionary containing bucket metrics
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get all blobs in the bucket
        blobs = list(bucket.list_blobs())
        
        # Calculate metrics
        total_objects = len(blobs)
        total_size = sum(blob.size or 0 for blob in blobs)
        
        # Group by storage class
        storage_class_stats = {}
        for blob in blobs:
            storage_class = blob.storage_class or 'STANDARD'
            if storage_class not in storage_class_stats:
                storage_class_stats[storage_class] = {'count': 0, 'size': 0}
            storage_class_stats[storage_class]['count'] += 1
            storage_class_stats[storage_class]['size'] += blob.size or 0
        
        # Calculate average object size
        avg_object_size = total_size / total_objects if total_objects > 0 else 0
        
        # Format size in human readable format
        def format_bytes(bytes_value):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.2f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.2f} PB"
        
        # Format storage class breakdown
        formatted_breakdown = {}
        for storage_class, stats in storage_class_stats.items():
            formatted_breakdown[storage_class] = {
                'count': stats['count'],
                'size': format_bytes(stats['size']),
                'size_bytes': stats['size'],
                'percentage': (stats['size'] / total_size * 100) if total_size > 0 else 0
            }
        
        return {
            "status": "success",
            "bucket_metrics": {
                "bucket_name": bucket_name,
                "total_objects": total_objects,
                "total_size": format_bytes(total_size),
                "total_size_bytes": total_size,
                "average_object_size": format_bytes(avg_object_size),
                "average_object_size_bytes": avg_object_size,
                "storage_class_breakdown": formatted_breakdown,
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get bucket metrics: {str(e)}"}

def view_bucket_cost_estimate(bucket_name: str):
    """
    View estimated costs for a bucket based on storage usage.
    
    Args:
        bucket_name: Name of the bucket to estimate costs for
        
    Returns:
        Dictionary containing cost estimates
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get all blobs in the bucket
        blobs = list(bucket.list_blobs())
        
        # Storage pricing (as of 2024, per GB per month)
        storage_pricing = {
            'STANDARD': 0.020,  # $0.020 per GB per month
            'NEARLINE': 0.010,  # $0.010 per GB per month
            'COLDLINE': 0.004,  # $0.004 per GB per month
            'ARCHIVE': 0.0012   # $0.0012 per GB per month
        }
        
        # Calculate costs by storage class
        total_cost = 0
        cost_breakdown = {}
        
        for blob in blobs:
            storage_class = blob.storage_class or 'STANDARD'
            size_gb = (blob.size or 0) / (1024**3)  # Convert bytes to GB
            
            if storage_class not in cost_breakdown:
                cost_breakdown[storage_class] = {'size_gb': 0, 'cost': 0}
            
            cost_breakdown[storage_class]['size_gb'] += size_gb
            cost_breakdown[storage_class]['cost'] += size_gb * storage_pricing.get(storage_class, storage_pricing['STANDARD'])
        
        # Calculate total cost
        for storage_class, data in cost_breakdown.items():
            total_cost += data['cost']
        
        # Format cost breakdown
        formatted_breakdown = {}
        for storage_class, data in cost_breakdown.items():
            formatted_breakdown[storage_class] = {
                'size_gb': round(data['size_gb'], 2),
                'monthly_cost': round(data['cost'], 4),
                'price_per_gb': storage_pricing.get(storage_class, storage_pricing['STANDARD'])
            }
        
        return {
            "status": "success",
            "cost_estimate": {
                "bucket_name": bucket_name,
                "total_monthly_cost": round(total_cost, 4),
                "total_annual_cost": round(total_cost * 12, 4),
                "cost_breakdown": formatted_breakdown,
                "currency": "USD",
                "pricing_note": "Based on standard Google Cloud Storage pricing (2024)",
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get cost estimate: {str(e)}"}

def monitor_access_logs(bucket_name: str, hours: int = 24):
    """
    Monitor access logs for a bucket.
    Note: This is a simplified implementation. For production, you'd want to use Cloud Logging.
    
    Args:
        bucket_name: Name of the bucket to monitor
        hours: Number of hours to look back
        
    Returns:
        Dictionary containing access log information
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get bucket metadata to check recent activity
        bucket.reload()
        
        # Get recent objects (as a proxy for activity)
        recent_objects = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for blob in bucket.list_blobs():
            if blob.updated and blob.updated.replace(tzinfo=None) > cutoff_time:
                recent_objects.append({
                    "name": blob.name,
                    "size": blob.size,
                    "updated": str(blob.updated),
                    "storage_class": blob.storage_class
                })
        
        # Sort by update time
        recent_objects.sort(key=lambda x: x['updated'], reverse=True)
        
        return {
            "status": "success",
            "access_logs": {
                "bucket_name": bucket_name,
                "monitoring_period_hours": hours,
                "recent_activity": {
                    "objects_modified": len(recent_objects),
                    "recent_objects": recent_objects[:10]  # Last 10 objects
                },
                "bucket_info": {
                    "created": str(bucket.time_created) if bucket.time_created else None,
                    "updated": str(bucket.updated) if bucket.updated else None,
                    "versioning_enabled": bucket.versioning_enabled
                },
                "note": "This is a simplified access log. For detailed logging, enable Cloud Logging for your bucket.",
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to monitor access logs: {str(e)}"}

# ===========================================
# WEBSITE HOSTING
# ===========================================

def enable_website_hosting(bucket_name: str, main_page_suffix: str = "index.html", 
                          not_found_page: str = "404.html"):
    """
    Enable website hosting for a bucket.
    
    This function:
    1. Configures the bucket's website settings
    2. Makes the bucket publicly accessible (required for website hosting)
    3. Sets proper CORS configuration
    
    Args:
        bucket_name: Name of the bucket to enable website hosting for
        main_page_suffix: Main page file (e.g., "index.html")
        not_found_page: 404 error page file (e.g., "404.html")
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        
        # CRITICAL FIX: Use get_bucket() instead of bucket() to fetch the actual bucket
        try:
            bucket = client.get_bucket(bucket_name)
        except Exception as e:
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist or cannot be accessed: {str(e)}"}
        
        # Step 1: Configure website settings using the proper API
        bucket.configure_website(
            main_page_suffix=main_page_suffix,
            not_found_page=not_found_page
        )
        
        # Step 2: Make the bucket publicly accessible (REQUIRED for website hosting)
        policy = bucket.get_iam_policy(requested_policy_version=3)
        
        # Check if already public
        already_public = False
        for binding in policy.bindings:
            if "allUsers" in binding.get("members", set()) and binding.get("role") == "roles/storage.objectViewer":
                already_public = True
                break
        
        if not already_public:
            # Add public read access
            policy.bindings.append({
                "role": "roles/storage.objectViewer",
                "members": {"allUsers"}
            })
            bucket.set_iam_policy(policy)
        
        # Step 3: Set CORS configuration to allow web access
        bucket.cors = [
            {
                "origin": ["*"],
                "method": ["GET", "HEAD"],
                "responseHeader": ["Content-Type"],
                "maxAgeSeconds": 3600
            }
        ]
        
        # Apply all changes
        bucket.patch()
        
        # Generate the website URL
        website_url = f"https://storage.googleapis.com/{bucket_name}/{main_page_suffix}"
        
        return {
            "status": "success",
            "message": f"Website hosting enabled for bucket '{bucket_name}'",
            "website_config": {
                "main_page_suffix": main_page_suffix,
                "not_found_page": not_found_page,
                "website_url": website_url,
                "public_url": f"https://storage.googleapis.com/{bucket_name}/",
                "note": "Bucket is now publicly accessible. All objects can be accessed via their URLs."
            },
            "next_steps": [
                f"Upload your website files to the bucket",
                f"Access your website at: {website_url}",
                "Optionally: Set up a custom domain using Cloud Load Balancer"
            ]
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to enable website hosting: {str(e)}",
            "troubleshooting": [
                "Ensure the bucket exists",
                "Verify you have storage.buckets.update permission",
                "Check that the Cloud Storage API is enabled",
                "Ensure your service account has sufficient permissions"
            ]
        }

def disable_website_hosting(bucket_name: str):
    """
    Disable website hosting for a bucket.
    
    Args:
        bucket_name: Name of the bucket to disable website hosting for
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        
        # CRITICAL FIX: Use get_bucket() instead of bucket()
        try:
            bucket = client.get_bucket(bucket_name)
        except Exception as e:
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist: {str(e)}"}
        
        # Clear website settings
        bucket.configure_website(main_page_suffix=None, not_found_page=None)
        
        # Remove public access
        policy = bucket.get_iam_policy(requested_policy_version=3)
        
        # Filter out the allUsers binding
        policy.bindings = [
            binding for binding in policy.bindings
            if "allUsers" not in binding.get("members", set())
        ]
        
        bucket.set_iam_policy(policy)
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Website hosting disabled for bucket '{bucket_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to disable website hosting: {str(e)}"}

def set_website_main_page(bucket_name: str, main_page_suffix: str):
    """
    Set the main page for website hosting.
    
    Args:
        bucket_name: Name of the bucket
        main_page_suffix: Main page file (e.g., "index.html")
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        
        # CRITICAL FIX: Use get_bucket() instead of bucket()
        try:
            bucket = client.get_bucket(bucket_name)
        except Exception as e:
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist: {str(e)}"}
        
        # Reload bucket to get current website configuration
        bucket.reload()
        
        # Get current not_found_page or use None
        current_not_found = None
        if hasattr(bucket, '_properties') and 'website' in bucket._properties:
            current_not_found = bucket._properties['website'].get('notFoundPage')
        
        # Update only the main page, preserve error page
        bucket.configure_website(main_page_suffix=main_page_suffix, not_found_page=current_not_found)
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Main page set to '{main_page_suffix}' for bucket '{bucket_name}'",
            "website_url": f"https://storage.googleapis.com/{bucket_name}/{main_page_suffix}"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set main page: {str(e)}"}

def set_website_error_page(bucket_name: str, not_found_page: str):
    """
    Set the error page for website hosting.
    
    Args:
        bucket_name: Name of the bucket
        not_found_page: 404 error page file (e.g., "404.html")
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        
        # CRITICAL FIX: Use get_bucket() instead of bucket()
        try:
            bucket = client.get_bucket(bucket_name)
        except Exception as e:
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist: {str(e)}"}
        
        # Reload bucket to get current website configuration
        bucket.reload()
        
        # Get current main_page_suffix or use default
        current_main_page = None
        if hasattr(bucket, '_properties') and 'website' in bucket._properties:
            current_main_page = bucket._properties['website'].get('mainPageSuffix')
        
        # Update only the error page, preserve main page
        bucket.configure_website(main_page_suffix=current_main_page, not_found_page=not_found_page)
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Error page set to '{not_found_page}' for bucket '{bucket_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set error page: {str(e)}"}

def upload_website_assets(bucket_name: str, assets_directory: str):
    """
    Upload website assets to a bucket.
    
    Args:
        bucket_name: Name of the bucket to upload assets to
        assets_directory: Local directory containing website assets
        
    Returns:
        Dictionary containing upload status and asset details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        if not os.path.exists(assets_directory):
            return {"status": "error", "message": f"Directory '{assets_directory}' does not exist"}
        
        uploaded_files = []
        
        # Walk through the directory and upload files
        for root, dirs, files in os.walk(assets_directory):
            for file in files:
                local_path = os.path.join(root, file)
                # Create object name by removing the assets_directory prefix
                relative_path = os.path.relpath(local_path, assets_directory)
                object_name = relative_path.replace(os.sep, '/')
                
                blob = bucket.blob(object_name)
                
                # Set content type based on file extension
                content_type = None
                if file.endswith('.html'):
                    content_type = 'text/html'
                elif file.endswith('.css'):
                    content_type = 'text/css'
                elif file.endswith('.js'):
                    content_type = 'application/javascript'
                elif file.endswith('.png'):
                    content_type = 'image/png'
                elif file.endswith('.jpg') or file.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                elif file.endswith('.gif'):
                    content_type = 'image/gif'
                elif file.endswith('.svg'):
                    content_type = 'image/svg+xml'
                
                if content_type:
                    blob.content_type = content_type
                
                blob.upload_from_filename(local_path)
                uploaded_files.append({
                    "object_name": object_name,
                    "size": blob.size,
                    "content_type": blob.content_type
                })
        
        return {
            "status": "success",
            "message": f"Uploaded {len(uploaded_files)} website assets to bucket '{bucket_name}'",
            "uploaded_files": uploaded_files,
            "website_url": f"https://storage.googleapis.com/{bucket_name}/"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to upload website assets: {str(e)}"}

def upload_html_content(bucket_name: str, filename: str, html_content: str):
    """
    Upload HTML content as a named file to a bucket.

    Use this when a user provides HTML code and wants it saved as a specific file
    (e.g. index.html, 404.html, about.html) in a GCS bucket for website hosting.

    Args:
        bucket_name: Name of the bucket to upload to
        filename: Name to give the file in the bucket (e.g. "index.html", "404.html")
        html_content: The raw HTML string to upload

    Returns:
        Dictionary containing upload status and the public URL of the uploaded file
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)

        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}

        blob = bucket.blob(filename)
        blob.upload_from_string(html_content, content_type='text/html')

        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
        return {
            "status": "success",
            "message": f"Successfully uploaded '{filename}' to bucket '{bucket_name}'",
            "filename": filename,
            "size_bytes": len(html_content.encode('utf-8')),
            "content_type": "text/html",
            "public_url": public_url,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to upload HTML content: {str(e)}"}


def set_cors_configuration(bucket_name: str, origins: List[str], methods: Optional[List[str]] = None,
                          headers: Optional[List[str]] = None, max_age: int = 3600):
    """
    Set CORS configuration for a bucket.
    
    Args:
        bucket_name: Name of the bucket
        origins: List of allowed origins (e.g., ['https://example.com', '*'])
        methods: List of allowed HTTP methods (default: ['GET', 'POST', 'PUT', 'DELETE'])
        headers: List of allowed headers (default: ['*'])
        max_age: Maximum age for preflight requests in seconds
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Set default values
        if methods is None:
            methods = ['GET', 'POST', 'PUT', 'DELETE']
        if headers is None:
            headers = ['*']
        
        # Configure CORS
        cors_rule = {
            "origin": origins,
            "method": methods,
            "responseHeader": headers,
            "maxAgeSeconds": max_age
        }
        
        bucket.cors = [cors_rule]
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"CORS configuration set for bucket '{bucket_name}'",
            "cors_config": cors_rule
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set CORS configuration: {str(e)}"}

def set_cache_control(bucket_name: str, object_name: str, cache_control: str):
    """
    Set cache control headers for an object.
    
    Args:
        bucket_name: Name of the bucket
        object_name: Name of the object
        cache_control: Cache control directive (e.g., "public, max-age=3600")
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        blob = bucket.blob(object_name)
        
        if not blob.exists():
            return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
        blob.cache_control = cache_control
        blob.patch()
        
        return {
            "status": "success",
            "message": f"Cache control set to '{cache_control}' for object '{object_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set cache control: {str(e)}"}

# ===========================================
# ADVANCED FEATURES
# ===========================================

def connect_to_bigquery_dataset(bucket_name: str, dataset_id: str, table_id: Optional[str] = None):
    """
    Connect bucket to BigQuery dataset for analytics and logging.
    
    Args:
        bucket_name: Name of the bucket
        dataset_id: BigQuery dataset ID
        table_id: Optional table ID (defaults to bucket_name)
        
    Returns:
        Dictionary containing connection status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        # Initialize BigQuery client
        bq_client = bigquery.Client(project=project_id, credentials=credentials)
        
        # Create dataset reference
        dataset_ref = bq_client.dataset(dataset_id)
        
        # Check if dataset exists, create if not
        try:
            bq_client.get_dataset(dataset_ref)
        except Exception:
            # Create dataset
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"  # Default location
            bq_client.create_dataset(dataset)
        
        # Set table ID
        if table_id is None:
            table_id = bucket_name.replace('-', '_')
        
        # Create table reference
        table_ref = dataset_ref.table(table_id)
        
        # Define table schema for bucket analytics
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("bucket_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("object_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("operation", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("size_bytes", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("storage_class", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("user_agent", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("ip_address", "STRING", mode="NULLABLE")
        ]
        
        # Create table if it doesn't exist
        try:
            bq_client.get_table(table_ref)
        except Exception:
            table = bigquery.Table(table_ref, schema=schema)
            bq_client.create_table(table)
        
        return {
            "status": "success",
            "message": f"Bucket '{bucket_name}' connected to BigQuery dataset '{dataset_id}'",
            "bigquery_config": {
                "project_id": project_id,
                "dataset_id": dataset_id,
                "table_id": table_id,
                "table_schema": [{"name": field.name, "type": field.field_type, "mode": field.mode} for field in schema]
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to connect to BigQuery: {str(e)}"}

def summarize_bucket_status(bucket_name: str):
    """
    Summarize all key information about a bucket.
    
    Args:
        bucket_name: Name of the bucket to summarize
        
    Returns:
        Dictionary containing comprehensive bucket summary
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get comprehensive bucket information
        bucket.reload()
        
        # Get objects
        blobs = list(bucket.list_blobs())
        
        # Calculate metrics
        total_objects = len(blobs)
        total_size = sum(blob.size or 0 for blob in blobs)
        
        # Storage class breakdown
        storage_class_stats = {}
        for blob in blobs:
            storage_class = blob.storage_class or 'STANDARD'
            if storage_class not in storage_class_stats:
                storage_class_stats[storage_class] = {'count': 0, 'size': 0}
            storage_class_stats[storage_class]['count'] += 1
            storage_class_stats[storage_class]['size'] += blob.size or 0
        
        # Get IAM policy
        try:
            policy = bucket.get_iam_policy()
            permissions = [{"role": binding["role"], "members": list(binding["members"])} for binding in policy.bindings]
        except Exception:
            permissions = []
        
        # Format size
        def format_bytes(bytes_value):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.2f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.2f} PB"
        
        # Cost estimation
        storage_pricing = {'STANDARD': 0.020, 'NEARLINE': 0.010, 'COLDLINE': 0.004, 'ARCHIVE': 0.0012}
        monthly_cost = 0
        for storage_class, stats in storage_class_stats.items():
            size_gb = stats['size'] / (1024**3)
            monthly_cost += size_gb * storage_pricing.get(storage_class, storage_pricing['STANDARD'])
        
        return {
            "status": "success",
            "bucket_summary": {
                "basic_info": {
                    "name": bucket.name,
                    "location": bucket.location,
                    "storage_class": bucket.storage_class,
                    "versioning_enabled": bucket.versioning_enabled,
                    "created": str(bucket.time_created) if bucket.time_created else None,
                    "updated": str(bucket.updated) if bucket.updated else None
                },
                "usage_stats": {
                    "total_objects": total_objects,
                    "total_size": format_bytes(total_size),
                    "total_size_bytes": total_size,
                    "average_object_size": format_bytes(total_size / total_objects) if total_objects > 0 else "0 B"
                },
                "storage_breakdown": {
                    storage_class: {
                        "count": stats['count'],
                        "size": format_bytes(stats['size']),
                        "percentage": (stats['size'] / total_size * 100) if total_size > 0 else 0
                    } for storage_class, stats in storage_class_stats.items()
                },
                "cost_estimate": {
                    "monthly_cost_usd": round(monthly_cost, 4),
                    "annual_cost_usd": round(monthly_cost * 12, 4)
                },
                "permissions": {
                    "total_bindings": len(permissions),
                    "permissions": permissions
                },
                "website_config": {
                    "enabled": bucket.website.main_page_suffix is not None,
                    "main_page": bucket.website.main_page_suffix,
                    "error_page": bucket.website.not_found_page,
                    "url": f"https://storage.googleapis.com/{bucket_name}/" if bucket.website.main_page_suffix else None
                },
                "security": {
                    "public_access_prevention": bucket.iam_configuration.public_access_prevention if bucket.iam_configuration else None,
                    "uniform_bucket_level_access": bucket.iam_configuration.uniform_bucket_level_access_enabled if bucket.iam_configuration else None
                },
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to summarize bucket status: {str(e)}"}

def recommend_storage_class(bucket_name: str):
    """
    Suggest cost-efficient storage types based on bucket usage patterns.
    
    Args:
        bucket_name: Name of the bucket to analyze
        
    Returns:
        Dictionary containing storage class recommendations
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get all objects
        blobs = list(bucket.list_blobs())
        
        if not blobs:
            return {
                "status": "success",
                "recommendations": {
                    "message": "No objects found in bucket. No specific recommendations available.",
                    "general_advice": "Consider using STANDARD storage class for frequently accessed data."
                }
            }
        
        # Analyze object access patterns
        now = datetime.utcnow()
        recent_objects = []
        old_objects = []
        
        for blob in blobs:
            if blob.updated:
                days_since_update = (now - blob.updated.replace(tzinfo=None)).days
                if days_since_update <= 30:
                    recent_objects.append(blob)
                else:
                    old_objects.append(blob)
        
        # Calculate size distribution
        total_size = sum(blob.size or 0 for blob in blobs)
        recent_size = sum(blob.size or 0 for blob in recent_objects)
        old_size = sum(blob.size or 0 for blob in old_objects)
        
        # Storage class recommendations
        recommendations = []
        
        # Recent data recommendation
        if recent_objects:
            recent_percentage = (recent_size / total_size * 100) if total_size > 0 else 0
            if recent_percentage > 70:
                recommendations.append({
                    "category": "Frequently Accessed Data",
                    "percentage": recent_percentage,
                    "recommendation": "STANDARD",
                    "reasoning": "High percentage of recently updated data suggests frequent access. STANDARD class provides best performance.",
                    "cost_impact": "Higher cost but optimal performance for active data"
                })
        
        # Old data recommendations
        if old_objects:
            old_percentage = (old_size / total_size * 100) if total_size > 0 else 0
            if old_percentage > 50:
                recommendations.append({
                    "category": "Infrequently Accessed Data",
                    "percentage": old_percentage,
                    "recommendation": "NEARLINE or COLDLINE",
                    "reasoning": "Large percentage of old data suggests infrequent access. Consider archival storage classes.",
                    "cost_impact": "Significant cost savings (50-80% reduction) for rarely accessed data"
                })
        
        # Size-based recommendations
        large_objects = [blob for blob in blobs if (blob.size or 0) > 100 * 1024 * 1024]  # > 100MB
        if large_objects:
            large_size = sum(blob.size or 0 for blob in large_objects)
            large_percentage = (large_size / total_size * 100) if total_size > 0 else 0
            recommendations.append({
                "category": "Large Objects",
                "percentage": large_percentage,
                "recommendation": "Consider COLDLINE or ARCHIVE for large, infrequently accessed files",
                "reasoning": "Large objects that are rarely accessed can benefit from archival storage classes.",
                "cost_impact": "Potential 60-95% cost reduction for large archival data"
            })
        
        # Cost analysis
        current_cost = 0
        optimized_cost = 0
        
        storage_pricing = {'STANDARD': 0.020, 'NEARLINE': 0.010, 'COLDLINE': 0.004, 'ARCHIVE': 0.0012}
        
        for blob in blobs:
            size_gb = (blob.size or 0) / (1024**3)
            current_storage_class = blob.storage_class or 'STANDARD'
            current_cost += size_gb * storage_pricing.get(current_storage_class, storage_pricing['STANDARD'])
            
            # Optimized storage class based on age
            if blob.updated:
                days_since_update = (now - blob.updated.replace(tzinfo=None)).days
                if days_since_update > 365:
                    optimized_storage_class = 'ARCHIVE'
                elif days_since_update > 90:
                    optimized_storage_class = 'COLDLINE'
                elif days_since_update > 30:
                    optimized_storage_class = 'NEARLINE'
                else:
                    optimized_storage_class = 'STANDARD'
            else:
                optimized_storage_class = 'ARCHIVE'  # No update time, assume old
            
            optimized_cost += size_gb * storage_pricing.get(optimized_storage_class, storage_pricing['STANDARD'])
        
        savings_percentage = ((current_cost - optimized_cost) / current_cost * 100) if current_cost > 0 else 0
        
        return {
            "status": "success",
            "storage_recommendations": {
                "bucket_name": bucket_name,
                "analysis_summary": {
                    "total_objects": len(blobs),
                    "total_size_gb": round(total_size / (1024**3), 2),
                    "recent_objects_percentage": round((len(recent_objects) / len(blobs) * 100), 2) if blobs else 0,
                    "old_objects_percentage": round((len(old_objects) / len(blobs) * 100), 2) if blobs else 0
                },
                "recommendations": recommendations,
                "cost_optimization": {
                    "current_monthly_cost": round(current_cost, 4),
                    "optimized_monthly_cost": round(optimized_cost, 4),
                    "potential_savings": round(current_cost - optimized_cost, 4),
                    "savings_percentage": round(savings_percentage, 2)
                },
                "implementation_notes": [
                    "Review each recommendation carefully before implementing",
                    "Consider data access patterns and business requirements",
                    "Test with a small subset before full migration",
                    "Monitor performance after changes"
                ],
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to generate storage recommendations: {str(e)}"}

# ===========================================
# BUCKET POLICY MANAGEMENT
# ===========================================

def get_bucket_policy(bucket_name: str):
    """
    Get the bucket policy configuration.
    
    Args:
        bucket_name: Name of the bucket
        
    Returns:
        Dictionary containing bucket policy details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        bucket.reload()
        
        return {
            "status": "success",
            "bucket_policy": {
                "bucket_name": bucket_name,
                "public_access_prevention": bucket.iam_configuration.public_access_prevention if bucket.iam_configuration else None,
                "uniform_bucket_level_access": bucket.iam_configuration.uniform_bucket_level_access_enabled if bucket.iam_configuration else None,
                "retention_policy": {
                    "retention_period": getattr(bucket.retention_policy, 'retention_period', None) if hasattr(bucket, 'retention_policy') and bucket.retention_policy else None,
                    "effective_time": str(getattr(bucket.retention_policy, 'effective_time', None)) if hasattr(bucket, 'retention_policy') and bucket.retention_policy and hasattr(bucket.retention_policy, 'effective_time') and bucket.retention_policy.effective_time else None
                } if hasattr(bucket, 'retention_policy') and bucket.retention_policy else None,
                "lifecycle_rules": [],
                "cors_configuration": [],
                "labels": dict(bucket.labels) if bucket.labels else {}
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get bucket policy: {str(e)}"}

def set_bucket_policy(bucket_name: str, public_access_prevention: Optional[str] = None, 
                     uniform_bucket_level_access: Optional[bool] = None):
    """
    Set bucket policy configuration.
    
    Args:
        bucket_name: Name of the bucket
        public_access_prevention: Public access prevention setting
        uniform_bucket_level_access: Enable/disable uniform bucket level access
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Update IAM configuration
        if not bucket.iam_configuration:
            bucket.iam_configuration = {}
        
        if public_access_prevention:
            bucket.iam_configuration.public_access_prevention = public_access_prevention
        
        if uniform_bucket_level_access is not None:
            bucket.iam_configuration.uniform_bucket_level_access_enabled = uniform_bucket_level_access
        
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Bucket policy updated for '{bucket_name}'",
            "updated_policy": {
                "public_access_prevention": bucket.iam_configuration.public_access_prevention,
                "uniform_bucket_level_access": bucket.iam_configuration.uniform_bucket_level_access_enabled
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set bucket policy: {str(e)}"}

def lock_bucket_policy(bucket_name: str, retention_period: int):
    """
    Lock bucket policy with retention period.
    
    Args:
        bucket_name: Name of the bucket
        retention_period: Retention period in seconds
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Set retention policy
        bucket.retention_policy = {
            "retention_period": retention_period,
            "effective_time": datetime.utcnow()
        }
        
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Bucket policy locked with {retention_period} seconds retention period",
            "retention_policy": {
                "retention_period": retention_period,
                "effective_time": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to lock bucket policy: {str(e)}"}

def get_bucket_iam_policy(bucket_name: str):
    """
    Get bucket IAM policy.
    
    Args:
        bucket_name: Name of the bucket
        
    Returns:
        Dictionary containing IAM policy
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        policy = bucket.get_iam_policy()
        
        return {
            "status": "success",
            "iam_policy": {
                "bucket_name": bucket_name,
                "bindings": [{"role": binding["role"], "members": list(binding["members"])} for binding in policy.bindings],
                "etag": policy.etag
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get bucket IAM policy: {str(e)}"}

def set_bucket_iam_policy(bucket_name: str, bindings: str):
    """
    Set bucket IAM policy.
    
    Args:
        bucket_name: Name of the bucket
        bindings: JSON string containing list of IAM bindings with role and members
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Parse bindings from JSON string
        try:
            bindings_list = json.loads(bindings)
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON format for bindings parameter"}
        
        # Create new policy
        policy = bucket.get_iam_policy()
        policy.bindings = bindings_list
        
        bucket.set_iam_policy(policy)
        
        return {
            "status": "success",
            "message": f"IAM policy updated for bucket '{bucket_name}'",
            "updated_bindings": bindings
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set bucket IAM policy: {str(e)}"}

def add_bucket_label(bucket_name: str, key: str, value: str):
    """
    Add a label to a bucket.
    
    Args:
        bucket_name: Name of the bucket
        key: Label key
        value: Label value
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Add label
        if not bucket.labels:
            bucket.labels = {}
        bucket.labels[key] = value
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Label '{key}: {value}' added to bucket '{bucket_name}'",
            "labels": dict(bucket.labels)
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to add bucket label: {str(e)}"}

def remove_bucket_label(bucket_name: str, key: str):
    """
    Remove a label from a bucket.
    
    Args:
        bucket_name: Name of the bucket
        key: Label key to remove
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Remove label
        if bucket.labels and key in bucket.labels:
            del bucket.labels[key]
            bucket.patch()
        
        return {
            "status": "success",
            "message": f"Label '{key}' removed from bucket '{bucket_name}'",
            "labels": dict(bucket.labels) if bucket.labels else {}
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to remove bucket label: {str(e)}"}

def set_bucket_lifecycle_rules(bucket_name: str, rules: str):
    """
    Set lifecycle rules for a bucket.
    
    Args:
        bucket_name: Name of the bucket
        rules: JSON string containing list of lifecycle rules
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Parse rules from JSON string
        try:
            rules_list = json.loads(rules)
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON format for rules parameter"}
        
        # Set lifecycle rules
        bucket.lifecycle_rules = rules_list
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Lifecycle rules set for bucket '{bucket_name}'",
            "rules": rules
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set bucket lifecycle rules: {str(e)}"}

# ===========================================
# ADVANCED OBJECT MANAGEMENT
# ===========================================

def update_object_metadata(bucket_name: str, object_name: str, metadata: Dict[str, str]):
    """
    Update metadata for an object.
    
    Args:
        bucket_name: Name of the bucket
        object_name: Name of the object
        metadata: Dictionary of metadata to update
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        blob = bucket.blob(object_name)
        
        if not blob.exists():
            return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
        # Update metadata
        blob.metadata = metadata
        blob.patch()
        
        return {
            "status": "success",
            "message": f"Metadata updated for object '{object_name}'",
            "updated_metadata": metadata
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to update object metadata: {str(e)}"}

def set_object_acl(bucket_name: str, object_name: str, entity: str, role: str):
    """
    Set ACL (Access Control List) for an object.
    
    Args:
        bucket_name: Name of the bucket
        object_name: Name of the object
        entity: Entity to grant access to (e.g., 'allUsers', 'allAuthenticatedUsers', 'user@example.com')
        role: Role to grant (e.g., 'READER', 'WRITER', 'OWNER')
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        blob = bucket.blob(object_name)
        
        if not blob.exists():
            return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
        # Set ACL
        blob.acl.entity(entity).grant(role)
        blob.acl.save()
        
        return {
            "status": "success",
            "message": f"ACL set for object '{object_name}': {entity} -> {role}",
            "acl_entry": {"entity": entity, "role": role}
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set object ACL: {str(e)}"}

def get_object_acl(bucket_name: str, object_name: str):
    """
    Get ACL (Access Control List) for an object.
    
    Args:
        bucket_name: Name of the bucket
        object_name: Name of the object
        
    Returns:
        Dictionary containing object ACL
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        blob = bucket.blob(object_name)
        
        if not blob.exists():
            return {"status": "error", "message": f"Object '{object_name}' does not exist in bucket '{bucket_name}'"}
        
        # Reload blob to get latest information
        try:
            blob.reload()
        except Exception as e:
            if "permission" in str(e).lower() or "access" in str(e).lower():
                return {"status": "error", "message": f"Permission denied: Cannot access object '{object_name}'. Service account needs 'storage.objects.get' permission."}
            else:
                return {"status": "error", "message": f"Failed to access object '{object_name}': {str(e)}"}
        
        # Get ACL
        acl_entries = []
        try:
            for entry in blob.acl:
                acl_entries.append({
                    "entity": str(entry.entity) if hasattr(entry, 'entity') else None,
                    "role": str(entry.role) if hasattr(entry, 'role') else None
                })
        except Exception as acl_error:
            return {
                "status": "error", 
                "message": f"Failed to retrieve ACL entries: {str(acl_error)}. This might be due to insufficient permissions or the object not having ACL configured."
            }
        
        return {
            "status": "success",
            "object_acl": {
                "bucket_name": bucket_name,
                "object_name": object_name,
                "acl_entries": acl_entries
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get object ACL: {str(e)}"}

def restore_object_version(bucket_name: str, object_name: str, generation: Optional[str] = None):
    """
    Restore a specific version of an object.
    
    Args:
        bucket_name: Name of the bucket
        object_name: Name of the object
        generation: Specific generation to restore (if None, restores latest)
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Check if versioning is enabled
        if not bucket.versioning_enabled:
            return {"status": "error", "message": f"Versioning is not enabled for bucket '{bucket_name}'"}
        
        # List object versions
        versions = list(bucket.list_blobs(prefix=object_name, versions=True))
        object_versions = [v for v in versions if v.name == object_name]
        
        if not object_versions:
            return {"status": "error", "message": f"No versions found for object '{object_name}'"}
        
        # Sort by generation (newest first)
        object_versions.sort(key=lambda x: x.generation, reverse=True)
        
        if generation:
            # Find specific version
            target_version = None
            for version in object_versions:
                if str(version.generation) == str(generation):
                    target_version = version
                    break
            
            if not target_version:
                return {"status": "error", "message": f"Version {generation} not found for object '{object_name}'"}
        else:
            # Use the latest version
            target_version = object_versions[0]
        
        # Copy the version to create a new current version
        new_blob = bucket.blob(object_name)
        new_blob.upload_from_string(target_version.download_as_bytes())
        
        # Copy metadata if it exists
        if target_version.metadata:
            new_blob.metadata = target_version.metadata
            new_blob.patch()
        
        return {
            "status": "success",
            "message": f"Object '{object_name}' restored from version {target_version.generation}",
            "restored_version": {
                "generation": target_version.generation,
                "created": str(target_version.time_created) if target_version.time_created else None,
                "size": target_version.size
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to restore object version: {str(e)}"}

# ===========================================
# ADVANCED ACCESS & SECURITY
# ===========================================

def audit_bucket_access(bucket_name: str, days: int = 7):
    """
    Audit bucket access patterns and permissions.
    
    Args:
        bucket_name: Name of the bucket
        days: Number of days to analyze
        
    Returns:
        Dictionary containing access audit results
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Get bucket IAM policy
        try:
            policy = bucket.get_iam_policy()
            iam_bindings = [{"role": binding["role"], "members": list(binding["members"])} for binding in policy.bindings]
        except Exception:
            iam_bindings = []
        
        # Get recent objects as proxy for activity
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        recent_objects = []
        
        for blob in bucket.list_blobs():
            if blob.updated and blob.updated.replace(tzinfo=None) > cutoff_time:
                recent_objects.append({
                    "name": blob.name,
                    "size": blob.size,
                    "updated": str(blob.updated),
                    "storage_class": blob.storage_class
                })
        
        # Analyze access patterns
        total_objects = len(list(bucket.list_blobs()))
        recent_count = len(recent_objects)
        activity_percentage = (recent_count / total_objects * 100) if total_objects > 0 else 0
        
        # Security analysis
        public_access = False
        for binding in iam_bindings:
            if "allUsers" in binding["members"] or "allAuthenticatedUsers" in binding["members"]:
                public_access = True
                break
        
        return {
            "status": "success",
            "access_audit": {
                "bucket_name": bucket_name,
                "analysis_period_days": days,
                "total_objects": total_objects,
                "recent_activity": {
                    "objects_modified": recent_count,
                    "activity_percentage": round(activity_percentage, 2),
                    "recent_objects": recent_objects[:10]  # Last 10 objects
                },
                "security_analysis": {
                    "public_access": public_access,
                    "iam_bindings_count": len(iam_bindings),
                    "uniform_bucket_level_access": bucket.iam_configuration.uniform_bucket_level_access_enabled if bucket.iam_configuration else None,
                    "public_access_prevention": bucket.iam_configuration.public_access_prevention if bucket.iam_configuration else None
                },
                "recommendations": [
                    "Review IAM bindings regularly" if len(iam_bindings) > 10 else None,
                    "Consider enabling uniform bucket level access" if not bucket.iam_configuration.uniform_bucket_level_access_enabled else None,
                    "Monitor for unusual access patterns" if activity_percentage > 50 else None
                ],
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to audit bucket access: {str(e)}"}

def set_uniform_bucket_level_access(bucket_name: str, enabled: bool):
    """
    Set uniform bucket level access for a bucket.
    
    Args:
        bucket_name: Name of the bucket
        enabled: Enable or disable uniform bucket level access
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Set uniform bucket level access
        if not bucket.iam_configuration:
            bucket.iam_configuration = {}
        
        bucket.iam_configuration.uniform_bucket_level_access_enabled = enabled
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Uniform bucket level access {'enabled' if enabled else 'disabled'} for bucket '{bucket_name}'",
            "uniform_bucket_level_access": enabled
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set uniform bucket level access: {str(e)}"}

# ===========================================
# ADVANCED MONITORING
# ===========================================

def enable_request_logging(bucket_name: str, log_bucket: Optional[str] = None):
    """
    Enable request logging for a bucket.
    
    Args:
        bucket_name: Name of the bucket to enable logging for
        log_bucket: Bucket to store logs in (defaults to same bucket)
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Set log bucket
        if log_bucket:
            log_bucket_obj = client.bucket(log_bucket)
            if not log_bucket_obj.exists():
                return {"status": "error", "message": f"Log bucket '{log_bucket}' does not exist"}
            bucket.logging.log_bucket = log_bucket
        else:
            bucket.logging.log_bucket = bucket_name
        
        # Set log object prefix
        bucket.logging.log_object_prefix = f"access-logs/{bucket_name}/"
        
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Request logging enabled for bucket '{bucket_name}'",
            "logging_config": {
                "log_bucket": bucket.logging.log_bucket,
                "log_object_prefix": bucket.logging.log_object_prefix
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to enable request logging: {str(e)}"}

def disable_request_logging(bucket_name: str):
    """
    Disable request logging for a bucket.
    
    Args:
        bucket_name: Name of the bucket to disable logging for
        
    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Clear logging configuration
        bucket.logging.log_bucket = None
        bucket.logging.log_object_prefix = None
        
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Request logging disabled for bucket '{bucket_name}'"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to disable request logging: {str(e)}"}

def analyze_bucket_activity(bucket_name: str, days: int = 30):
    """
    Analyze bucket activity patterns and provide insights.
    
    Args:
        bucket_name: Name of the bucket to analyze
        days: Number of days to analyze
        
    Returns:
        Dictionary containing activity analysis
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Analyze objects by creation/update time
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # Get all objects
        all_objects = list(bucket.list_blobs())
        
        # Categorize objects by activity
        recent_count = 0
        old_count = 0
        large_count = 0
        small_count = 0
        
        total_size = 0
        storage_class_distribution = {}
        
        for blob in all_objects:
            total_size += blob.size or 0
            
            # Categorize by age
            if blob.updated and blob.updated.replace(tzinfo=None) > cutoff_time:
                recent_count += 1
            else:
                old_count += 1
            
            # Categorize by size
            if (blob.size or 0) > 100 * 1024 * 1024:  # > 100MB
                large_count += 1
            else:
                small_count += 1
            
            # Count by storage class
            storage_class = blob.storage_class or 'STANDARD'
            storage_class_distribution[storage_class] = storage_class_distribution.get(storage_class, 0) + 1
        
        # Calculate metrics
        total_objects = len(all_objects)
        
        # Activity patterns
        activity_percentage = (recent_count / total_objects * 100) if total_objects > 0 else 0
        large_object_percentage = (large_count / total_objects * 100) if total_objects > 0 else 0
        
        # Storage efficiency analysis
        def format_bytes(bytes_value):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.2f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.2f} PB"
        
        # Generate insights
        insights = []
        recommendations = []
        
        if activity_percentage < 10:
            insights.append("Low activity bucket - most objects are not recently accessed")
            recommendations.append("Consider moving old objects to cheaper storage classes")
        
        if large_object_percentage > 20:
            insights.append("High percentage of large objects")
            recommendations.append("Consider compression or chunking for large files")
        
        if storage_class_distribution.get('STANDARD', 0) / total_objects > 0.8:
            insights.append("Most objects are in STANDARD storage class")
            recommendations.append("Review storage class distribution for cost optimization")
        
        return {
            "status": "success",
            "activity_analysis": {
                "bucket_name": bucket_name,
                "analysis_period_days": days,
                "summary": {
                    "total_objects": total_objects,
                    "total_size": format_bytes(total_size),
                    "total_size_bytes": total_size,
                    "average_object_size": format_bytes(total_size / total_objects) if total_objects > 0 else "0 B"
                },
                "activity_patterns": {
                    "recent_objects": recent_count,
                    "old_objects": old_count,
                    "activity_percentage": round(activity_percentage, 2),
                    "large_objects": large_count,
                    "small_objects": small_count,
                    "large_object_percentage": round(large_object_percentage, 2)
                },
                "storage_distribution": storage_class_distribution,
                "insights": insights,
                "recommendations": recommendations,
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to analyze bucket activity: {str(e)}"}

# ===========================================
# ADVANCED OPERATIONS
# ===========================================

def sync_local_directory_to_bucket(bucket_name: str, local_directory: str, 
                                 destination_prefix: str = "", exclude_patterns: Optional[List[str]] = None):
    """
    Sync a local directory to a bucket.
    
    Args:
        bucket_name: Name of the bucket
        local_directory: Local directory to sync
        destination_prefix: Prefix for objects in bucket
        exclude_patterns: List of patterns to exclude
        
    Returns:
        Dictionary containing sync results
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        if not os.path.exists(local_directory):
            return {"status": "error", "message": f"Local directory '{local_directory}' does not exist"}
        
        uploaded_files = []
        skipped_files = []
        
        # Walk through directory
        for root, dirs, files in os.walk(local_directory):
            for file in files:
                local_path = os.path.join(root, file)
                
                # Check exclude patterns
                should_exclude = False
                if exclude_patterns:
                    for pattern in exclude_patterns:
                        if pattern in local_path:
                            should_exclude = True
                            break
                
                if should_exclude:
                    skipped_files.append(local_path)
                    continue
                
                # Create object name
                relative_path = os.path.relpath(local_path, local_directory)
                object_name = f"{destination_prefix}{relative_path}".replace(os.sep, '/')
                
                # Upload file
                blob = bucket.blob(object_name)
                
                # Set content type based on extension
                content_type = None
                if file.endswith('.html'):
                    content_type = 'text/html'
                elif file.endswith('.css'):
                    content_type = 'text/css'
                elif file.endswith('.js'):
                    content_type = 'application/javascript'
                elif file.endswith('.json'):
                    content_type = 'application/json'
                elif file.endswith('.png'):
                    content_type = 'image/png'
                elif file.endswith('.jpg') or file.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                
                if content_type:
                    blob.content_type = content_type
                
                blob.upload_from_filename(local_path)
                uploaded_files.append({
                    "local_path": local_path,
                    "object_name": object_name,
                    "size": blob.size,
                    "content_type": blob.content_type
                })
        
        return {
            "status": "success",
            "message": f"Synced {len(uploaded_files)} files to bucket '{bucket_name}'",
            "sync_results": {
                "uploaded_files": uploaded_files,
                "skipped_files": skipped_files,
                "total_uploaded": len(uploaded_files),
                "total_skipped": len(skipped_files)
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to sync directory: {str(e)}"}

def backup_bucket_to_another_bucket(source_bucket: str, destination_bucket: str, 
                                   destination_prefix: str = ""):
    """
    Backup a bucket to another bucket.
    
    Args:
        source_bucket: Name of the source bucket
        destination_bucket: Name of the destination bucket
        destination_prefix: Prefix for objects in destination bucket
        
    Returns:
        Dictionary containing backup results
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        
        # Check source bucket
        source_bucket_obj = client.bucket(source_bucket)
        if not source_bucket_obj.exists():
            return {"status": "error", "message": f"Source bucket '{source_bucket}' does not exist"}
        
        # Check destination bucket
        dest_bucket_obj = client.bucket(destination_bucket)
        if not dest_bucket_obj.exists():
            return {"status": "error", "message": f"Destination bucket '{destination_bucket}' does not exist"}
        
        # Copy objects
        copied_objects = []
        failed_objects = []
        
        for blob in source_bucket_obj.list_blobs():
            try:
                # Create destination object name
                dest_object_name = f"{destination_prefix}{blob.name}"
                
                # Copy object
                source_bucket_obj.copy_blob(blob, dest_bucket_obj, dest_object_name)
                
                copied_objects.append({
                    "source_name": blob.name,
                    "destination_name": dest_object_name,
                    "size": blob.size
                })
            except Exception as e:
                failed_objects.append({
                    "object_name": blob.name,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "message": f"Backup completed: {len(copied_objects)} objects copied",
            "backup_results": {
                "copied_objects": copied_objects,
                "failed_objects": failed_objects,
                "total_copied": len(copied_objects),
                "total_failed": len(failed_objects)
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to backup bucket: {str(e)}"}

def migrate_bucket_to_different_region(source_bucket: str, destination_bucket: str, 
                                     destination_region: str):
    """
    Migrate a bucket to a different region.
    
    Args:
        source_bucket: Name of the source bucket
        destination_bucket: Name of the destination bucket
        destination_region: Target region for migration
        
    Returns:
        Dictionary containing migration results
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        
        # Check source bucket
        source_bucket_obj = client.bucket(source_bucket)
        if not source_bucket_obj.exists():
            return {"status": "error", "message": f"Source bucket '{source_bucket}' does not exist"}
        
        # Create destination bucket in new region
        dest_bucket_obj = client.bucket(destination_bucket)
        if not dest_bucket_obj.exists():
            dest_bucket_obj = client.create_bucket(destination_bucket, location=destination_region)
        
        # Copy all objects
        migrated_objects = []
        failed_objects = []
        
        for blob in source_bucket_obj.list_blobs():
            try:
                # Copy object to destination bucket
                source_bucket_obj.copy_blob(blob, dest_bucket_obj, blob.name)
                migrated_objects.append({
                    "object_name": blob.name,
                    "size": blob.size
                })
            except Exception as e:
                failed_objects.append({
                    "object_name": blob.name,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "message": f"Migration completed: {len(migrated_objects)} objects migrated to {destination_region}",
            "migration_results": {
                "migrated_objects": migrated_objects,
                "failed_objects": failed_objects,
                "total_migrated": len(migrated_objects),
                "total_failed": len(failed_objects),
                "destination_region": destination_region
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to migrate bucket: {str(e)}"}

def archive_old_objects(bucket_name: str, days_old: int = 365, 
                       target_storage_class: str = "ARCHIVE"):
    """
    Archive old objects to a different storage class.
    
    Args:
        bucket_name: Name of the bucket
        days_old: Age threshold in days
        target_storage_class: Target storage class for archiving
        
    Returns:
        Dictionary containing archiving results
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Find old objects
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)
        old_objects = []
        
        for blob in bucket.list_blobs():
            if blob.updated and blob.updated.replace(tzinfo=None) < cutoff_time:
                old_objects.append(blob)
        
        # Archive objects
        archived_objects = []
        failed_objects = []
        
        for blob in old_objects:
            try:
                # Create new blob with different storage class
                new_blob = bucket.blob(blob.name)
                new_blob.upload_from_string(blob.download_as_bytes())
                new_blob.storage_class = target_storage_class
                new_blob.patch()
                
                # Delete old blob
                blob.delete()
                
                archived_objects.append({
                    "object_name": blob.name,
                    "size": blob.size,
                    "new_storage_class": target_storage_class
                })
            except Exception as e:
                failed_objects.append({
                    "object_name": blob.name,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "message": f"Archived {len(archived_objects)} objects to {target_storage_class} storage class",
            "archiving_results": {
                "archived_objects": archived_objects,
                "failed_objects": failed_objects,
                "total_archived": len(archived_objects),
                "total_failed": len(failed_objects),
                "target_storage_class": target_storage_class
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to archive old objects: {str(e)}"}

def schedule_periodic_cleanup(bucket_name: str, cleanup_rules: str):
    """
    Schedule periodic cleanup based on rules.
    
    Args:
        bucket_name: Name of the bucket
        cleanup_rules: JSON string containing list of cleanup rules
        
    Returns:
        Dictionary containing cleanup schedule
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Parse cleanup rules from JSON string
        try:
            cleanup_rules_list = json.loads(cleanup_rules)
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON format for cleanup_rules parameter"}
        
        # Set lifecycle rules for cleanup
        bucket.lifecycle_rules = cleanup_rules_list
        bucket.patch()
        
        return {
            "status": "success",
            "message": f"Periodic cleanup scheduled for bucket '{bucket_name}'",
            "cleanup_schedule": {
                "bucket_name": bucket_name,
                "rules": cleanup_rules,
                "scheduled_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to schedule periodic cleanup: {str(e)}"}

def trigger_cloud_function_on_event(bucket_name: str, function_name: str, 
                                   event_type: str = "finalize"):
    """
    Configure bucket to trigger cloud function on events.
    
    Args:
        bucket_name: Name of the bucket
        function_name: Name of the cloud function
        event_type: Type of event to trigger on
        
    Returns:
        Dictionary containing trigger configuration
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}
        
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}
        
        # Note: This is a simplified implementation
        # In practice, you would use Cloud Functions API to set up the trigger
        
        return {
            "status": "success",
            "message": f"Cloud function trigger configured for bucket '{bucket_name}'",
            "trigger_config": {
                "bucket_name": bucket_name,
                "function_name": function_name,
                "event_type": event_type,
                "note": "This is a simplified implementation. Use Cloud Functions API for full configuration."
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to configure cloud function trigger: {str(e)}"}


# =============================================================================
# CATEGORY A: RETENTION POLICIES
# =============================================================================

def set_retention_policy(bucket_name: str, retention_period_seconds: int):
    """
    Set a retention policy on a bucket to enforce a minimum retention period for all objects.

    Args:
        bucket_name: Name of the bucket
        retention_period_seconds: Minimum retention period in seconds (e.g., 2592000 = 30 days)

    Returns:
        Dictionary containing operation status and retention policy details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        bucket.retention_period = retention_period_seconds
        bucket.patch()

        days = retention_period_seconds / 86400
        return {
            "status": "success",
            "message": f"Retention policy set on bucket '{bucket_name}': {retention_period_seconds}s ({days:.1f} days)",
            "bucket_name": bucket_name,
            "retention_period_seconds": retention_period_seconds,
            "retention_period_days": round(days, 2),
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set retention policy: {str(e)}"}


def get_retention_policy(bucket_name: str):
    """
    Get the retention policy configuration for a bucket.

    Args:
        bucket_name: Name of the bucket

    Returns:
        Dictionary containing retention policy details and lock status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        if bucket.retention_period is None:
            return {
                "status": "success",
                "message": f"No retention policy configured on bucket '{bucket_name}'",
                "bucket_name": bucket_name,
                "retention_policy": None,
            }

        return {
            "status": "success",
            "message": f"Retention policy found for bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "retention_policy": {
                "retention_period_seconds": bucket.retention_period,
                "retention_period_days": round(bucket.retention_period / 86400, 2),
                "policy_locked": bucket.retention_policy_locked,
                "effective_time": bucket.retention_policy_effective_time.isoformat() if bucket.retention_policy_effective_time else None,
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get retention policy: {str(e)}"}


def remove_retention_policy(bucket_name: str):
    """
    Remove the retention policy from a bucket. Only allowed if the policy is not locked.

    Args:
        bucket_name: Name of the bucket

    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        if bucket.retention_policy_locked:
            return {
                "status": "error",
                "message": f"Cannot remove retention policy from '{bucket_name}': policy is locked. Locked policies cannot be removed or shortened.",
            }

        if bucket.retention_period is None:
            return {
                "status": "success",
                "message": f"No retention policy to remove on bucket '{bucket_name}'",
            }

        bucket.retention_period = None
        bucket.patch()

        return {
            "status": "success",
            "message": f"Retention policy removed from bucket '{bucket_name}'",
            "bucket_name": bucket_name,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to remove retention policy: {str(e)}"}


# =============================================================================
# CATEGORY B: OBJECT HOLDS
# =============================================================================

def set_temporary_hold(bucket_name: str, object_name: str):
    """
    Place a temporary hold on an object. Objects on hold cannot be deleted or replaced
    until the hold is released.

    Args:
        bucket_name: Name of the bucket
        object_name: Name of the object to hold

    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        blob = bucket.get_blob(object_name)

        if blob is None:
            return {"status": "error", "message": f"Object '{object_name}' not found in bucket '{bucket_name}'"}

        blob.temporary_hold = True
        blob.patch()

        return {
            "status": "success",
            "message": f"Temporary hold placed on '{object_name}' in bucket '{bucket_name}'. Object cannot be deleted until hold is released.",
            "bucket_name": bucket_name,
            "object_name": object_name,
            "temporary_hold": True,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set temporary hold: {str(e)}"}


def release_temporary_hold(bucket_name: str, object_name: str):
    """
    Release a temporary hold from an object, allowing it to be deleted or overwritten.

    Args:
        bucket_name: Name of the bucket
        object_name: Name of the object

    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        blob = bucket.get_blob(object_name)

        if blob is None:
            return {"status": "error", "message": f"Object '{object_name}' not found in bucket '{bucket_name}'"}

        blob.temporary_hold = False
        blob.patch()

        return {
            "status": "success",
            "message": f"Temporary hold released from '{object_name}' in bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "object_name": object_name,
            "temporary_hold": False,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to release temporary hold: {str(e)}"}


def set_event_based_hold(bucket_name: str, object_name: str):
    """
    Place an event-based hold on an object. The hold must be released before the object can be
    deleted, and the retention period (if set) starts only after the hold is released.

    Args:
        bucket_name: Name of the bucket
        object_name: Name of the object to hold

    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        blob = bucket.get_blob(object_name)

        if blob is None:
            return {"status": "error", "message": f"Object '{object_name}' not found in bucket '{bucket_name}'"}

        blob.event_based_hold = True
        blob.patch()

        return {
            "status": "success",
            "message": f"Event-based hold placed on '{object_name}' in bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "object_name": object_name,
            "event_based_hold": True,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set event-based hold: {str(e)}"}


def release_event_based_hold(bucket_name: str, object_name: str):
    """
    Release an event-based hold from an object. Once released, the object's retention period
    starts counting.

    Args:
        bucket_name: Name of the bucket
        object_name: Name of the object

    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        blob = bucket.get_blob(object_name)

        if blob is None:
            return {"status": "error", "message": f"Object '{object_name}' not found in bucket '{bucket_name}'"}

        blob.event_based_hold = False
        blob.patch()

        return {
            "status": "success",
            "message": f"Event-based hold released from '{object_name}' in bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "object_name": object_name,
            "event_based_hold": False,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to release event-based hold: {str(e)}"}


def set_default_event_based_hold(bucket_name: str, enabled: bool = True):
    """
    Enable or disable default event-based hold for all new objects created in a bucket.
    When enabled, all new objects will automatically have an event-based hold applied.

    Args:
        bucket_name: Name of the bucket
        enabled: True to enable default event-based hold, False to disable

    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        bucket.default_event_based_hold = enabled
        bucket.patch()

        action = "enabled" if enabled else "disabled"
        return {
            "status": "success",
            "message": f"Default event-based hold {action} on bucket '{bucket_name}'. {'All new objects will have event-based hold automatically.' if enabled else 'New objects will not have automatic event-based holds.'}",
            "bucket_name": bucket_name,
            "default_event_based_hold": enabled,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set default event-based hold: {str(e)}"}


# =============================================================================
# CATEGORY C: CMEK ENCRYPTION
# =============================================================================

def set_bucket_encryption(bucket_name: str, kms_key_name: str):
    """
    Set a Customer-Managed Encryption Key (CMEK) as the default encryption key for a bucket.
    All new objects will be encrypted with this key.

    Args:
        bucket_name: Name of the bucket
        kms_key_name: Full resource name of the KMS key, e.g.:
                      projects/PROJECT_ID/locations/LOCATION/keyRings/KEY_RING/cryptoKeys/KEY_NAME

    Returns:
        Dictionary containing operation status and encryption configuration
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        bucket.default_kms_key_name = kms_key_name
        bucket.patch()

        return {
            "status": "success",
            "message": f"CMEK encryption key set on bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "kms_key_name": kms_key_name,
            "note": "All new objects uploaded to this bucket will be encrypted with the specified CMEK key.",
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to set bucket encryption: {str(e)}"}


def get_bucket_encryption(bucket_name: str):
    """
    Get the current encryption configuration for a bucket.

    Args:
        bucket_name: Name of the bucket

    Returns:
        Dictionary containing encryption configuration details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        kms_key = bucket.default_kms_key_name

        if kms_key:
            encryption_type = "Customer-Managed Encryption Key (CMEK)"
            key_info = kms_key
        else:
            encryption_type = "Google-Managed Encryption Key (GMEK)"
            key_info = "Managed by Google Cloud KMS automatically"

        return {
            "status": "success",
            "message": f"Encryption configuration for bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "encryption_type": encryption_type,
            "kms_key_name": kms_key,
            "description": key_info,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get bucket encryption: {str(e)}"}


def remove_bucket_encryption(bucket_name: str):
    """
    Remove the Customer-Managed Encryption Key (CMEK) from a bucket, reverting to
    Google-managed encryption. Existing objects retain their current encryption.

    Args:
        bucket_name: Name of the bucket

    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        if not bucket.default_kms_key_name:
            return {
                "status": "success",
                "message": f"Bucket '{bucket_name}' already uses Google-managed encryption. No changes made.",
            }

        bucket.default_kms_key_name = None
        bucket.patch()

        return {
            "status": "success",
            "message": f"CMEK removed from bucket '{bucket_name}'. New objects will use Google-managed encryption.",
            "bucket_name": bucket_name,
            "note": "Existing objects encrypted with the CMEK key remain encrypted with that key unless re-uploaded.",
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to remove bucket encryption: {str(e)}"}


# =============================================================================
# CATEGORY D: PUB/SUB NOTIFICATIONS
# =============================================================================

def create_bucket_notification(bucket_name: str, topic_name: str, event_types: str = "all"):
    """
    Create a Pub/Sub notification for bucket events. The GCS service account must have
    permission to publish to the topic.

    Args:
        bucket_name: Name of the bucket
        topic_name: Full Pub/Sub topic name, e.g.: projects/PROJECT_ID/topics/TOPIC_NAME
        event_types: Comma-separated event types, or 'all' for all events.
                     Valid types: OBJECT_FINALIZE, OBJECT_METADATA_UPDATE, OBJECT_DELETE, OBJECT_ARCHIVE

    Returns:
        Dictionary containing notification configuration and ID
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        valid_event_types = ["OBJECT_FINALIZE", "OBJECT_METADATA_UPDATE", "OBJECT_DELETE", "OBJECT_ARCHIVE"]
        if event_types.lower() == "all":
            chosen_event_types = None  # None means all events
        else:
            chosen_event_types = [e.strip().upper() for e in event_types.split(",")]
            invalid = [e for e in chosen_event_types if e not in valid_event_types]
            if invalid:
                return {
                    "status": "error",
                    "message": f"Invalid event types: {invalid}. Valid options: {valid_event_types}"
                }

        notification = bucket.notification(
            topic_name=topic_name,
            event_types=chosen_event_types,
            payload_format="JSON_API_V1",
        )
        notification.create()

        return {
            "status": "success",
            "message": f"Pub/Sub notification created for bucket '{bucket_name}' -> topic '{topic_name}'",
            "bucket_name": bucket_name,
            "topic_name": topic_name,
            "notification_id": notification.notification_id,
            "event_types": chosen_event_types or "ALL",
            "payload_format": "JSON_API_V1",
            "note": "Ensure the GCS service account has roles/pubsub.publisher on the topic.",
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to create bucket notification: {str(e)}"}


def list_bucket_notifications(bucket_name: str):
    """
    List all active Pub/Sub notification configurations for a bucket.

    Args:
        bucket_name: Name of the bucket

    Returns:
        Dictionary containing list of notification configurations
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        notifications = list(bucket.list_notifications())

        notification_list = []
        for n in notifications:
            notification_list.append({
                "notification_id": n.notification_id,
                "topic_name": n.topic_name,
                "event_types": n.event_types or "ALL",
                "payload_format": n.payload_format,
                "custom_attributes": n.custom_attributes,
            })

        return {
            "status": "success",
            "message": f"Found {len(notification_list)} notification(s) for bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "notifications": notification_list,
            "count": len(notification_list),
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list bucket notifications: {str(e)}"}


def delete_bucket_notification(bucket_name: str, notification_id: str):
    """
    Delete a specific Pub/Sub notification configuration from a bucket.

    Args:
        bucket_name: Name of the bucket
        notification_id: ID of the notification to delete (from list_bucket_notifications)

    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        notification = bucket.get_notification(notification_id)
        notification.delete()

        return {
            "status": "success",
            "message": f"Notification '{notification_id}' deleted from bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "notification_id": notification_id,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete bucket notification: {str(e)}"}


# =============================================================================
# CATEGORY E: SOFT DELETE
# =============================================================================

def enable_soft_delete(bucket_name: str, retention_duration_days: int = 7):
    """
    Enable soft delete on a bucket so that deleted objects are retained for a recovery window
    before permanent deletion.

    Args:
        bucket_name: Name of the bucket
        retention_duration_days: Number of days to retain soft-deleted objects (1-90, default 7)

    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        if not (1 <= retention_duration_days <= 90):
            return {"status": "error", "message": "retention_duration_days must be between 1 and 90"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        retention_seconds = retention_duration_days * 86400
        bucket.soft_delete_policy.retention_duration_seconds = retention_seconds
        bucket.patch()

        return {
            "status": "success",
            "message": f"Soft delete enabled on bucket '{bucket_name}' with {retention_duration_days}-day retention window",
            "bucket_name": bucket_name,
            "retention_duration_days": retention_duration_days,
            "retention_duration_seconds": retention_seconds,
            "note": "Deleted objects will be recoverable for the specified window before permanent deletion.",
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to enable soft delete: {str(e)}"}


def disable_soft_delete(bucket_name: str):
    """
    Disable soft delete on a bucket. Deleted objects will be permanently deleted immediately.

    Args:
        bucket_name: Name of the bucket

    Returns:
        Dictionary containing operation status
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.get_bucket(bucket_name)

        bucket.soft_delete_policy.retention_duration_seconds = 0
        bucket.patch()

        return {
            "status": "success",
            "message": f"Soft delete disabled on bucket '{bucket_name}'. Deleted objects will be permanently removed immediately.",
            "bucket_name": bucket_name,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to disable soft delete: {str(e)}"}


def list_soft_deleted_objects(bucket_name: str, prefix: str = ""):
    """
    List objects that have been soft-deleted from a bucket and are within the recovery window.

    Args:
        bucket_name: Name of the bucket
        prefix: Optional prefix to filter objects

    Returns:
        Dictionary containing list of soft-deleted objects with their generation numbers
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)

        kwargs = {"bucket_or_name": bucket_name, "soft_deleted": True}
        if prefix:
            kwargs["prefix"] = prefix

        blobs = list(client.list_blobs(**kwargs))

        object_list = []
        for blob in blobs:
            object_list.append({
                "name": blob.name,
                "generation": blob.generation,
                "size": blob.size,
                "time_deleted": blob.time_deleted.isoformat() if blob.time_deleted else None,
            })

        return {
            "status": "success",
            "message": f"Found {len(object_list)} soft-deleted object(s) in bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "soft_deleted_objects": object_list,
            "count": len(object_list),
            "note": "Use restore_soft_deleted_object with the generation number to recover an object.",
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list soft-deleted objects: {str(e)}"}


def restore_soft_deleted_object(bucket_name: str, object_name: str, generation: str, restore_name: str = ""):
    """
    Restore a soft-deleted object by its generation number. The object will be restored
    to its original name or a new name if specified.

    Args:
        bucket_name: Name of the bucket
        object_name: Name of the soft-deleted object
        generation: Generation number of the soft-deleted object (from list_soft_deleted_objects)
        restore_name: New name for the restored object (defaults to original name)

    Returns:
        Dictionary containing operation status and restored object details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)

        target_name = restore_name if restore_name else object_name

        source_blob = bucket.blob(object_name)
        source_blob._properties["generation"] = str(generation)

        new_blob = bucket.copy_blob(source_blob, bucket, target_name)

        return {
            "status": "success",
            "message": f"Soft-deleted object '{object_name}' (generation {generation}) restored as '{target_name}' in bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "original_name": object_name,
            "restored_name": target_name,
            "generation_restored": generation,
            "restored_size": new_blob.size,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to restore soft-deleted object: {str(e)}"}


# =============================================================================
# CATEGORY F: BATCH OPERATIONS
# =============================================================================

def batch_delete_objects(bucket_name: str, object_names: str):
    """
    Delete multiple objects from a bucket in a single batch operation.

    Args:
        bucket_name: Name of the bucket
        object_names: JSON array of object names to delete, e.g.: ["file1.txt", "file2.txt"]

    Returns:
        Dictionary containing operation results with success and failure counts
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        try:
            names_list = json.loads(object_names)
            if not isinstance(names_list, list):
                raise ValueError("Must be a JSON array")
        except (json.JSONDecodeError, ValueError) as e:
            return {"status": "error", "message": f"object_names must be a valid JSON array: {str(e)}"}

        if not names_list:
            return {"status": "error", "message": "object_names array is empty"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)

        deleted = []
        failed = []

        with client.batch():
            for name in names_list:
                try:
                    blob = bucket.blob(name)
                    blob.delete()
                    deleted.append(name)
                except Exception as e:
                    failed.append({"name": name, "error": str(e)})

        return {
            "status": "success" if not failed else "partial",
            "message": f"Batch delete complete: {len(deleted)} deleted, {len(failed)} failed",
            "bucket_name": bucket_name,
            "deleted_count": len(deleted),
            "failed_count": len(failed),
            "deleted": deleted,
            "failed": failed,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to batch delete objects: {str(e)}"}


def batch_copy_objects(source_bucket: str, destination_bucket: str, prefix: str = "", destination_prefix: str = ""):
    """
    Copy all objects matching a prefix from one bucket to another.

    Args:
        source_bucket: Name of the source bucket
        destination_bucket: Name of the destination bucket
        prefix: Optional prefix to filter source objects (e.g., "logs/" copies all logs)
        destination_prefix: Optional prefix to prepend to objects in the destination bucket

    Returns:
        Dictionary containing copy results with success and failure counts
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        src_bucket = client.bucket(source_bucket)
        dst_bucket = client.bucket(destination_bucket)

        if not dst_bucket.exists():
            return {"status": "error", "message": f"Destination bucket '{destination_bucket}' does not exist"}

        kwargs = {}
        if prefix:
            kwargs["prefix"] = prefix

        blobs = list(client.list_blobs(source_bucket, **kwargs))

        if not blobs:
            return {
                "status": "success",
                "message": f"No objects found in '{source_bucket}' with prefix '{prefix}'",
                "copied_count": 0,
            }

        copied = []
        failed = []

        for blob in blobs:
            try:
                dest_name = destination_prefix + blob.name if destination_prefix else blob.name
                src_bucket.copy_blob(blob, dst_bucket, dest_name)
                copied.append({"source": blob.name, "destination": dest_name})
            except Exception as e:
                failed.append({"name": blob.name, "error": str(e)})

        return {
            "status": "success" if not failed else "partial",
            "message": f"Batch copy complete: {len(copied)} copied, {len(failed)} failed",
            "source_bucket": source_bucket,
            "destination_bucket": destination_bucket,
            "prefix_filter": prefix or "(all objects)",
            "copied_count": len(copied),
            "failed_count": len(failed),
            "copied": copied[:20],
            "failed": failed,
            "total_objects_found": len(blobs),
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to batch copy objects: {str(e)}"}


def compose_objects(bucket_name: str, source_objects: str, destination_object: str):
    """
    Compose (merge) multiple objects into a single object. Useful for assembling large files
    uploaded in parallel chunks. Maximum 32 source objects per compose operation.

    Args:
        bucket_name: Name of the bucket containing all objects
        source_objects: JSON array of source object names in order, e.g.: ["chunk-1", "chunk-2"]
        destination_object: Name of the composed output object

    Returns:
        Dictionary containing operation status and composed object details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        try:
            source_list = json.loads(source_objects)
            if not isinstance(source_list, list):
                raise ValueError("Must be a JSON array")
        except (json.JSONDecodeError, ValueError) as e:
            return {"status": "error", "message": f"source_objects must be a valid JSON array: {str(e)}"}

        if len(source_list) < 2:
            return {"status": "error", "message": "At least 2 source objects are required for compose"}

        if len(source_list) > 32:
            return {"status": "error", "message": "Maximum 32 source objects per compose operation"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)

        source_blobs = [bucket.blob(name) for name in source_list]
        destination_blob = bucket.blob(destination_object)
        destination_blob.compose(source_blobs)

        destination_blob.reload()

        return {
            "status": "success",
            "message": f"Composed {len(source_list)} objects into '{destination_object}' in bucket '{bucket_name}'",
            "bucket_name": bucket_name,
            "source_objects": source_list,
            "destination_object": destination_object,
            "composed_size_bytes": destination_blob.size,
            "composed_size_kb": round(destination_blob.size / 1024, 2) if destination_blob.size else None,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to compose objects: {str(e)}"}


# =============================================================================
# CATEGORY G: RESUMABLE LARGE FILE UPLOAD
# =============================================================================

def upload_large_object_resumable(bucket_name: str, source_file_path: str, destination_blob_name: str, chunk_size_mb: int = 8):
    """
    Upload a large file to GCS using resumable upload with configurable chunk size.
    Automatically retries on network failure. Ideal for files larger than 100MB.

    Args:
        bucket_name: Name of the destination bucket
        source_file_path: Local path to the file to upload
        destination_blob_name: Name for the object in GCS
        chunk_size_mb: Chunk size in MB for resumable upload (default 8MB)

    Returns:
        Dictionary containing upload status and object details
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        if not os.path.exists(source_file_path):
            return {"status": "error", "message": f"Source file not found: {source_file_path}"}

        file_size = os.path.getsize(source_file_path)

        # Chunk size must be a multiple of 256KB (262144 bytes)
        chunk_size_bytes = chunk_size_mb * 1024 * 1024
        chunk_size_bytes = ((chunk_size_bytes + 262143) // 262144) * 262144

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)

        if not bucket.exists():
            return {"status": "error", "message": f"Bucket '{bucket_name}' does not exist"}

        blob = bucket.blob(destination_blob_name)
        blob.chunk_size = chunk_size_bytes  # Enables resumable upload mode

        blob.upload_from_filename(
            source_file_path,
            timeout=600,
            num_retries=5,
        )

        blob.reload()

        return {
            "status": "success",
            "message": f"File '{source_file_path}' uploaded as '{destination_blob_name}' in bucket '{bucket_name}' using resumable upload",
            "bucket_name": bucket_name,
            "object_name": destination_blob_name,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "chunk_size_bytes": chunk_size_bytes,
            "content_type": blob.content_type,
            "generation": blob.generation,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to upload large file: {str(e)}"}


# =============================================================================
# CATEGORY H: INVENTORY REPORTS
# =============================================================================

def create_inventory_report(source_bucket: str, destination_bucket: str, destination_path: str = "inventory", frequency: str = "weekly"):
    """
    Create a Storage Insights inventory report or generate a one-time CSV inventory.
    Uses the Storage Insights API if available; falls back to a manual CSV generation.

    Args:
        source_bucket: Name of the bucket to inventory
        destination_bucket: Name of the bucket where reports will be stored
        destination_path: Path prefix in destination bucket for reports (default: "inventory")
        frequency: Report frequency - "daily" or "weekly" (default: "weekly")

    Returns:
        Dictionary containing report configuration or manual inventory listing
    """
    try:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project

        try:
            from google.cloud import storageinsights_v1

            insights_client = storageinsights_v1.StorageInsightsClient(credentials=credentials)
            parent = f"projects/{project_id}/locations/global"

            freq_value = (
                storageinsights_v1.FrequencyOptions.Frequency.WEEKLY
                if frequency == "weekly"
                else storageinsights_v1.FrequencyOptions.Frequency.DAILY
            )

            report_config = storageinsights_v1.ReportConfig(
                csv_options=storageinsights_v1.CSVOptions(
                    record_separator="\n",
                    delimiter=",",
                    header_required=True,
                ),
                object_metadata_report_options=storageinsights_v1.ObjectMetadataReportOptions(
                    metadata_fields=["project", "bucket", "name", "size", "timeCreated", "updated", "storageClass"],
                    storage_filters=storageinsights_v1.CloudStorageFilters(bucket=source_bucket),
                    storage_destination_options=storageinsights_v1.CloudStorageDestinationOptions(
                        bucket=destination_bucket,
                        destination_path=destination_path,
                    ),
                ),
                frequency_options=storageinsights_v1.FrequencyOptions(
                    frequency=freq_value,
                    start_date={"year": datetime.now().year, "month": datetime.now().month, "day": datetime.now().day},
                    end_date={"year": datetime.now().year + 1, "month": datetime.now().month, "day": datetime.now().day},
                ),
            )

            request = storageinsights_v1.CreateReportConfigRequest(parent=parent, report_config=report_config)
            response = insights_client.create_report_config(request=request)

            return {
                "status": "success",
                "message": f"Scheduled inventory report configured: '{source_bucket}' -> '{destination_bucket}/{destination_path}'",
                "source_bucket": source_bucket,
                "destination_bucket": destination_bucket,
                "destination_path": destination_path,
                "frequency": frequency,
                "report_config_name": response.name,
                "method": "Storage Insights API",
            }

        except ImportError:
            # Fallback: generate a one-time CSV inventory
            client = storage.Client(project=project_id, credentials=credentials)
            blobs = list(client.list_blobs(source_bucket))

            csv_lines = ["name,size,storage_class,time_created,updated,content_type"]
            for blob in blobs:
                csv_lines.append(
                    f"{blob.name},{blob.size},{blob.storage_class},"
                    f"{blob.time_created.isoformat() if blob.time_created else ''},"
                    f"{blob.updated.isoformat() if blob.updated else ''},"
                    f"{blob.content_type or ''}"
                )

            csv_content = "\n".join(csv_lines)
            report_name = f"{destination_path}/inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            dst_bucket = client.bucket(destination_bucket)
            report_blob = dst_bucket.blob(report_name)
            report_blob.upload_from_string(csv_content, content_type="text/csv")

            return {
                "status": "success",
                "message": f"One-time inventory report for '{source_bucket}' saved to '{destination_bucket}/{report_name}'",
                "source_bucket": source_bucket,
                "destination_bucket": destination_bucket,
                "report_path": report_name,
                "object_count": len(blobs),
                "method": "manual_csv",
                "note": "For scheduled reports, install: pip install google-cloud-storageinsights",
            }

    except Exception as e:
        return {"status": "error", "message": f"Failed to create inventory report: {str(e)}"}


def list_inventory_reports(project_id_override: str = ""):
    """
    List all configured Storage Insights inventory report configurations in the project.
    Requires the google-cloud-storageinsights package.

    Args:
        project_id_override: Optional project ID override (defaults to GOOGLE_CLOUD_PROJECT env var)

    Returns:
        Dictionary containing list of inventory report configurations
    """
    try:
        project_id = project_id_override or os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            return {"status": "error", "message": "GOOGLE_CLOUD_PROJECT environment variable not set"}

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            return {"status": "error", "message": "GCP credentials not found"}

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project and not project_id_override:
            project_id = auth_project

        try:
            from google.cloud import storageinsights_v1

            insights_client = storageinsights_v1.StorageInsightsClient(credentials=credentials)
            parent = f"projects/{project_id}/locations/global"

            request = storageinsights_v1.ListReportConfigsRequest(parent=parent)
            configs = list(insights_client.list_report_configs(request=request))

            report_list = []
            for config in configs:
                report_list.append({
                    "name": config.name,
                    "display_name": getattr(config, "display_name", ""),
                    "create_time": config.create_time.isoformat() if config.create_time else None,
                    "update_time": config.update_time.isoformat() if config.update_time else None,
                })

            return {
                "status": "success",
                "message": f"Found {len(report_list)} inventory report configuration(s)",
                "project_id": project_id,
                "report_configs": report_list,
                "count": len(report_list),
            }

        except ImportError:
            return {
                "status": "error",
                "message": "google-cloud-storageinsights package not installed.",
                "note": "Install with: pip install google-cloud-storageinsights",
            }

    except Exception as e:
        return {"status": "error", "message": f"Failed to list inventory reports: {str(e)}"}