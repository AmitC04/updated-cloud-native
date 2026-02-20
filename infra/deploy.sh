#!/bin/bash
# infra/deploy.sh
# Deployment script for YouTube Pipeline on Google Cloud Run

set -e  # Exit on any error

echo "🚀 Starting YouTube Pipeline deployment to Google Cloud Run..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Validate required environment variables
REQUIRED_VARS=(
    "GCP_PROJECT_ID"
    "GCP_REGION" 
    "MONGO_URI"
    "MONGO_DB_NAME"
    "YOUTUBE_API_KEY"
    "GEMINI_API_KEY"
    "API_KEY"
    "WEBHOOK_SECRET"
    "WEBHOOK_BASE_URL"
    "CHANNEL_IDS"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set. Please set all required environment variables in .env"
        exit 1
    fi
done

SERVICE_NAME="youtube-pipeline"
IMAGE_NAME="youtube-pipeline"

echo "🔧 Building container image..."
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/$IMAGE_NAME --project=$GCP_PROJECT_ID

echo "📦 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$GCP_PROJECT_ID/$IMAGE_NAME \
    --platform managed \
    --region $GCP_REGION \
    --project $GCP_PROJECT_ID \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300s \
    --concurrency 80 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars MONGO_URI=$MONGO_URI \
    --set-env-vars MONGO_DB_NAME=$MONGO_DB_NAME \
    --set-env-vars YOUTUBE_API_KEY=$YOUTUBE_API_KEY \
    --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
    --set-env-vars API_KEY=$API_KEY \
    --set-env-vars WEBHOOK_SECRET=$WEBHOOK_SECRET \
    --set-env-vars PUBSUB_HUB_URL="https://pubsubhubbub.appspot.com/subscribe" \
    --set-env-vars WEBHOOK_BASE_URL=$WEBHOOK_BASE_URL \
    --set-env-vars CHANNEL_IDS=$CHANNEL_IDS \
    --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID \
    --set-env-vars GCP_REGION=$GCP_REGION \
    --allow-unauthenticated

echo "🌐 Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $GCP_REGION --project $GCP_PROJECT_ID --format 'value(status.url)')

echo "✅ Service deployed successfully!"
echo "Service URL: $SERVICE_URL"

# Update webhook base URL in environment
export WEBHOOK_BASE_URL=$SERVICE_URL
sed -i.bak "s|WEBHOOK_BASE_URL=.*|WEBHOOK_BASE_URL=$SERVICE_URL|" .env || echo "Could not update .env file automatically"

echo "🔄 Running initial subscription to YouTube channels..."
python -m ingestion.subscribe

echo "📊 Running initial bulk ingestion..."
python -m ingestion.bulk_ingest --limit 100

echo "📋 Deployment summary:"
echo "  - Service: $SERVICE_NAME"
echo "  - Region: $GCP_REGION" 
echo "  - URL: $SERVICE_URL"
echo "  - Status: Ready to receive webhook notifications and serve API requests"

echo "💡 Next steps:"
echo "  1. Your webhook is now listening at $SERVICE_URL/webhook"
echo "  2. Your API is available at $SERVICE_URL/api/"
echo "  3. Test the API: curl $SERVICE_URL/videos/recent"
echo "  4. Chatbot UI: Access via Cloud Run service URL when running separately"

echo "🎉 YouTube Pipeline deployment complete!"