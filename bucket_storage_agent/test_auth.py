#!/usr/bin/env python3
"""
Test Google Cloud Storage authentication
"""

import os
import json
from dotenv import load_dotenv

def test_authentication():
    """Test GCP authentication and configuration."""
    
    print("🔐 Testing Google Cloud Storage Authentication...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    print(f"📋 Project ID: {project_id if project_id else '❌ NOT SET'}")
    print(f"🔑 Credentials Path: {creds_path if creds_path else '❌ NOT SET'}")
    
    if not project_id:
        print("\n❌ ERROR: GOOGLE_CLOUD_PROJECT not set in .env file!")
        return False
    
    if not creds_path:
        print("\n❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS not set in .env file!")
        return False
    
    # Check if credentials file exists
    if not os.path.exists(creds_path):
        print(f"\n❌ ERROR: Credentials file not found: {creds_path}")
        print("Please check the path in your .env file.")
        return False
    
    print(f"✅ Credentials file exists: {creds_path}")
    
    # Test authentication
    try:
        from google.auth import default
        from google.cloud import storage
        
        print("\n🔑 Testing authentication...")
        credentials, auth_project = default()
        print(f"✅ Authentication successful!")
        print(f"📍 Authenticated project: {auth_project}")
        
        # Test storage client with timeout (cross-platform)
        print("\n🗄️  Testing Storage Client...")
        import threading
        import time
        
        def test_storage_with_timeout():
            try:
                client = storage.Client(project=project_id, credentials=credentials)
                print("⏳ Attempting to list buckets (30s timeout)...")
                buckets = list(client.list_buckets())
                return buckets, None
            except Exception as e:
                return None, e
        
        # Use threading for timeout on Windows
        result_container = [None]
        error_container = [None]
        
        def run_test():
            try:
                buckets, error = test_storage_with_timeout()
                result_container[0] = buckets
                error_container[0] = error
            except Exception as e:
                error_container[0] = e
        
        # Start the test in a separate thread
        test_thread = threading.Thread(target=run_test)
        test_thread.daemon = True
        test_thread.start()
        
        # Wait for 30 seconds
        test_thread.join(timeout=30)
        
        if test_thread.is_alive():
            print(f"⏰ Storage client operation timed out after 30 seconds")
            print("💡 This usually means:")
            print("   - Cloud Storage API is not enabled in your project")
            print("   - Network connectivity issues")
            print("   - Service account lacks 'storage.buckets.list' permission")
            print("\n🔧 Solutions:")
            print("   1. Enable Cloud Storage API: https://console.cloud.google.com/apis/library/storage.googleapis.com")
            print("   2. Check service account permissions in IAM")
            print("   3. Verify network connectivity")
            return False
        
        # Check results
        if error_container[0]:
            print(f"⚠️  Storage client created but cannot list buckets: {error_container[0]}")
            print("💡 This might be due to insufficient permissions")
            return False
        
        buckets = result_container[0]
        if buckets is not None:
            print(f"✅ Storage client working!")
            print(f"📦 Found {len(buckets)} buckets")
            
            if buckets:
                print("📋 Available buckets:")
                for bucket in buckets[:3]:  # Show first 3
                    print(f"   - {bucket.name}")
                if len(buckets) > 3:
                    print(f"   ... and {len(buckets) - 3} more")
            else:
                print("ℹ️  No buckets found (normal for new projects)")
        else:
            print("❌ Unexpected error occurred")
            return False
            
    except ImportError as e:
        print(f"\n❌ ERROR: Missing packages: {e}")
        print("Please install: pip install google-cloud-storage google-auth python-dotenv")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: Authentication failed: {e}")
        print("💡 Common solutions:")
        print("   - Check if your service account key is valid")
        print("   - Verify the service account has required permissions")
        print("   - Ensure Storage API is enabled in your project")
        return False
    
    print("\n🎉 SUCCESS: Authentication is working!")
    print("Your GCP Storage Agent should now work properly.")
    return True

if __name__ == "__main__":
    test_authentication()

