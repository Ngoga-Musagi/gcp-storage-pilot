#!/usr/bin/env python3
"""
Create .env file for GCP Storage Agent
"""

import os
import json

def create_env_file():
    """Create .env file with proper configuration."""
    
    print("🔧 Creating .env file for GCP Storage Agent...")
    
    # Check if service account key exists
    key_file = "service-account-key.json"
    if not os.path.exists(key_file):
        print(f"❌ ERROR: {key_file} not found!")
        print("Please run the setup script first: ./setup_service_account.sh")
        return False
    
    # Read project ID from the key file
    try:
        with open(key_file, 'r') as f:
            key_data = json.load(f)
            project_id = key_data.get('project_id', 'your-project-id-here')
    except Exception as e:
        print(f"❌ ERROR: Could not read {key_file}: {e}")
        return False
    
    # Create .env content
    env_content = f"""# Google Cloud Storage Agent Configuration
GOOGLE_CLOUD_PROJECT={project_id}
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
DEFAULT_BUCKET=my-default-bucket
DEFAULT_REGION=US
DEFAULT_STORAGE_CLASS=STANDARD
"""
    
    # Write .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print(f"📋 Project ID: {project_id}")
        print(f"🔑 Credentials: ./service-account-key.json")
        return True
    except Exception as e:
        print(f"❌ ERROR: Could not create .env file: {e}")
        return False

if __name__ == "__main__":
    create_env_file()

