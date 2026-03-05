#!/usr/bin/env python3
"""
Test bucket access and permissions for GCP Storage Agent
"""

import os
from dotenv import load_dotenv
from google.auth import default
from google.cloud import storage

def test_bucket_access(bucket_name):
    """Test if a bucket exists and if we have proper permissions."""
    
    print(f"🔍 Testing access to bucket: {bucket_name}")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not project_id:
        print("❌ ERROR: GOOGLE_CLOUD_PROJECT not set")
        return False
    
    if not creds_path or not os.path.exists(creds_path):
        print("❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS not set or file not found")
        return False
    
    print(f"📋 Project: {project_id}")
    print(f"🔑 Credentials: {creds_path}")
    
    try:
        # Set up client
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        credentials, auth_project = default()
        if auth_project:
            project_id = auth_project
        
        client = storage.Client(project=project_id, credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        print(f"\n🔍 Testing bucket existence...")
        
        # Test 1: Check if bucket exists
        if not bucket.exists():
            print(f"❌ Bucket '{bucket_name}' does not exist")
            print("💡 You can create it with: Create a bucket named 'my-website-assets'")
            return False
        
        print(f"✅ Bucket '{bucket_name}' exists")
        
        # Test 2: Check basic access
        print(f"\n🔍 Testing basic bucket access...")
        try:
            bucket.reload()
            print(f"✅ Basic bucket access works")
        except Exception as e:
            print(f"❌ Basic access failed: {e}")
            return False
        
        # Test 3: Check IAM policy access
        print(f"\n🔍 Testing IAM policy access...")
        try:
            policy = bucket.get_iam_policy()
            print(f"✅ IAM policy access works")
            print(f"📋 Found {len(policy.bindings)} IAM bindings")
        except Exception as e:
            print(f"❌ IAM policy access failed: {e}")
            print("💡 Service account needs 'storage.buckets.getIamPolicy' permission")
            return False
        
        # Test 4: Check object listing
        print(f"\n🔍 Testing object listing...")
        try:
            objects = list(bucket.list_blobs(max_results=5))
            print(f"✅ Object listing works")
            print(f"📦 Found {len(objects)} objects (showing first 5)")
        except Exception as e:
            print(f"❌ Object listing failed: {e}")
            print("💡 Service account needs 'storage.objects.list' permission")
            return False
        
        print(f"\n🎉 All tests passed! Bucket '{bucket_name}' is accessible.")
        return True
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def main():
    """Test bucket access for common bucket names."""
    
    # Test common bucket names
    test_buckets = [
        "my-website-assets",
        "my-website-assets123", 
        "test-bucket",
        "storage-bucket"
    ]
    
    print("🧪 Testing bucket access for GCP Storage Agent")
    print("=" * 60)
    
    for bucket_name in test_buckets:
        print(f"\n{'='*20} Testing {bucket_name} {'='*20}")
        test_bucket_access(bucket_name)
        print()

if __name__ == "__main__":
    main()










