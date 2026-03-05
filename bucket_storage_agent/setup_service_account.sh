#!/bin/bash
# GCP Storage Agent - Service Account Setup
set -e

echo "🔐 Setting up GCP Storage Agent..."

# Check prerequisites
command -v gcloud >/dev/null || { echo "❌ Install gcloud CLI first"; exit 1; }
gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q . || { echo "❌ Run: gcloud auth login"; exit 1; }

# Get project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
[ -z "$PROJECT_ID" ] && { echo "❌ Set project: gcloud config set project YOUR_PROJECT_ID"; exit 1; }

echo "📋 Project: $PROJECT_ID"

# Setup variables
SA_NAME="storage-agent-service-account"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
KEY_FILE="service-account-key.json"

# Create service account
echo "🔧 Creating service account..."
gcloud iam service-accounts create $SA_NAME \
    --display-name="GCP Storage Agent" \
    --description="Service account for GCP Storage Agent" \
    --project=$PROJECT_ID 2>/dev/null || echo "⚠️  Service account may already exist"

# Assign roles
echo "🔑 Assigning roles..."
for role in storage.admin storage.objectAdmin storage.objectViewer monitoring.viewer bigquery.dataEditor; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/$role" --quiet
done

# Download key
echo "🔑 Downloading key..."
gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SA_EMAIL --project=$PROJECT_ID

# Create .env
echo "📝 Creating .env..."
cat > .env << EOF
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_APPLICATION_CREDENTIALS=./$KEY_FILE
DEFAULT_BUCKET=my-default-bucket
DEFAULT_REGION=US
DEFAULT_STORAGE_CLASS=STANDARD
EOF

echo "✅ Setup complete!"
echo "🎉 Service Account: $SA_EMAIL"
echo "🔑 Key File: $KEY_FILE"
echo "📝 Config: .env"
echo ""
echo "🚀 Next: python test_credentials.py"
