# YouTube Pipeline - Cloud-Native AI Data Engineer Project

## Overview
This project implements an automated real-time pipeline that monitors high-frequency YouTube channels and captures metadata for each new video as soon as it's published. The system operates in near real-time using WebSub (PubSubHubbub) webhooks to avoid slow, periodic polling methods that waste serverless infrastructure and API calls.

## Architecture
```
YouTube Channels → PubSubHubbub Webhooks → Google Cloud Run → MongoDB Atlas → FastAPI REST API → Streamlit AI Chatbot
```

## Tech Stack
- **Backend**: Python, FastAPI
- **Database**: MongoDB Atlas
- **Cloud Platform**: Google Cloud Run (Serverless)
- **AI Framework**: Google ADK with Gemini API
- **Frontend**: Streamlit Dashboard
- **Data Extraction**: yt-dlp
- **Real-time Notifications**: PubSubHubbub (WebSub)

## Features

### 1. Real-Time Data Capture
- Uses PubSubHubbub (WebSub) to receive instant notifications when new videos are published
- No polling - eliminates unnecessary API calls and server load
- Handles multiple YouTube channels simultaneously

### 2. Data Storage & Schema
- Stores video metadata in MongoDB Atlas with proper indexing
- Schema includes required fields plus additional metadata for AI analysis:
```json
{
  "video_id": "string",
  "title": "string", 
  "url": "string",
  "upload_date": "string", // ISO 8601 format
  "view_count": "integer",
  "like_count": "integer", 
  "description": "string",
  "channel_id": "string",
  "channel": "string",
  "channel_url": "string",
  "duration": "integer",
  "thumbnail": "string",
  "tags": "array",
  "comment_count": "integer",
  "ingested_at": "string",
  "source": "string"
}
```

### 3. Target Channels
- Monitors high-frequency channels including:
  - Bloomberg Markets (@markets)
  - ANI News India (@ANINewsIndia)
- Supports adding more high-frequency channels across different time zones

### 4. Bulk Ingestion
- Downloads most recent 1000 videos from target channels using yt-dlp
- Performs rate limiting to respect YouTube's terms of service

### 5. Serverless API
- Deployed on Google Cloud Run (serverless)
- Secured REST API with token-based authentication
- Endpoints for querying video metadata

### 6. Agentic AI Chatbot
- Streamlit-based chatbot interface
- Powered by Google ADK and Gemini API
- Implements specialized tools for specific queries:
  - Count videos from specific channels
  - Find videos about specific topics in date ranges
  - Other analytical capabilities

## Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB Atlas account
- Google Cloud account with billing enabled
- YouTube Data API v3 key
- Google Gemini API key

### Environment Variables
Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required values:
- `MONGO_URI`: MongoDB Atlas connection string
- `YOUTUBE_API_KEY`: YouTube Data API v3 key
- `GEMINI_API_KEY`: Google Gemini API key
- `API_KEY`: Static API key for securing endpoints
- `WEBHOOK_SECRET`: Secret for verifying webhook signatures
- `GCP_PROJECT_ID`: Your Google Cloud Project ID
- `CHANNEL_IDS`: YouTube channel IDs (obtained using get_channel_ids.py)

### Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### 1. Get Channel IDs
```bash
python ingestion/get_channel_ids.py
```
This will output the channel IDs that you need to add to your .env file.

### 2. Bulk Ingest Historical Data
```bash
python ingestion/bulk_ingest.py
```
This will download metadata for the most recent 1000 videos from each channel.

### 3. Subscribe to Real-Time Notifications
```bash
python ingestion/subscribe.py
```
This subscribes to YouTube channels for real-time video notifications.

### 4. Run the API Server
```bash
python -m main api
```
The API will be available at http://localhost:8000

### 5. Run the Webhook Server
```bash
python -m main webhook
```
The webhook will listen at http://localhost:8080/webhook

### 6. Run the Chatbot
```bash
streamlit run chatbot/app.py
```
The chatbot UI will be available at http://localhost:8501

## API Endpoints

### Authentication
All API endpoints require an API key in the Authorization header:
```
Authorization: Bearer YOUR_API_KEY
```

### Available Endpoints
- `GET /` - Health check
- `GET /health` - Health status
- `GET /videos/search?q=SEARCH_TERM&channel=CHANNEL&limit=LIMIT` - Search videos
- `GET /videos/recent?limit=LIMIT&channel=CHANNEL` - Get recent videos
- `GET /videos/popular?limit=LIMIT&days=DAYS` - Get popular videos
- `GET /channels/list` - List all channels
- `GET /videos/stats` - Get database statistics
- `GET /videos/{video_id}` - Get specific video
- `GET /most_recent` - Get most recent entries (for assessment)

## Assessment-Specific Features

### Query Script
The `query_db.py` module includes a function `get_most_recent_entries()` that returns the most recently added entries to test if the webhook and data ingestion pipelines work correctly.

### Agentic AI Capabilities
The chatbot implements the following specific tools for the assessment:

1. **Channel Video Counter**: Answers "How many videos from markets (Bloomberg Television) channel have we saved in our database?"
2. **Topic-Based Time Filter**: Answers "Give me a count of the videos published about USA in ANINEWSIndia channel in the last 24 hrs?"

These tools use MongoDB queries to analyze the stored metadata and provide accurate answers to natural language questions.

## Deployment

### Google Cloud Run Deployment
Use the provided deployment script:
```bash
bash infra/deploy.sh
```

This will:
- Build a container image
- Deploy to Google Cloud Run
- Configure environment variables
- Run initial subscription to YouTube channels
- Perform bulk ingestion of 100 videos

## Security
- Token-based authentication for API endpoints
- Webhook signature verification
- Environment variables for sensitive data
- Rate limiting to prevent abuse

## Scalability
- Serverless architecture scales automatically
- MongoDB Atlas provides horizontal scaling
- PubSubHubbub handles notification delivery
- Configurable rate limits for ingestion

## Bonus Features
- Secured API with token-based authentication
- Comprehensive error handling
- Logging and monitoring ready
- Flexible configuration via environment variables
- Support for multiple high-frequency channels