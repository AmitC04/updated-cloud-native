# 🎬 YouTube Intelligence Hub - CloudNative AI Assessment Solution

![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![MongoDB](https://img.shields.io/badge/mongodb-atlas-green)

**Production-ready cloud-native real-time YouTube data pipeline** with Agentic AI capabilities.

## ✨ Key Highlights

- ✅ **Real-time PubSubHubbub webhooks** (zero polling)
- ✅ **MongoDB Atlas** cloud database
- ✅ **Agentic AI chatbot** (Gemini + tool use)
- ✅ **Streamlit UI** (beautiful dark theme)
- ✅ **REST API** (secured with API key)
- ✅ **Serverless deployment** ready

## 🎯 Features

### ✅ Real-Time Data Ingestion
- **PubSubHubbub (WebSub)** integration for instant video notifications
- **Zero polling** - eliminates wasteful API calls
- **Automatic subscription management** with renewal logic
- Monitors multiple YouTube channels simultaneously

### 📊 Cloud Database Storage
- **MongoDB Atlas** cloud database integration
- Strict schema with required fields + metadata
- Automatic indexing on `upload_date`, `channel_id`, and text search
- Connection via environment variables

### 🤖 Agentic AI Chatbot
- **Google Generative AI** (Gemini) integration
- **Tool-enabled agent** that automatically:
  - Counts videos by channel
  - Fetches videos from last 24 hours
  - Searches by topic
  - Searches by country
  - Generates trending topics
  - Retrieves database statistics
- Conversational Streamlit UI

### 🔗 REST API Endpoints
- `/latest` - Get latest videos
- `/last24h` - Videos from last 24 hours
- `/channel/{name}` - Videos from specific channel
- `/search?q=` - Full-text search
- `/videos/popular` - Popular videos by views
- `/stats` - Database statistics
- `/health` - Service health check

### 🚀 Deployment Ready
- Docker containerization
- Docker Compose for local development
- Google Cloud Run deployment script
- CI/CD ready

---

## 📐 Architecture

```
YouTube Channels (Bloomberg Markets, ANI News India)
            ↓
    PubSubHubbub Hub
            ↓
    Webhook Server (Flask/FastAPI)
            ↓
    Video Metadata Extraction (yt-dlp)
            ↓
    MongoDB Atlas (Cloud Database)
            ↓
    ├─ REST API Server (FastAPI) → External clients/UI
    ├─ Streamlit Chatbot UI → Web browser
    └─ Query Scripts → CLI tools
```

### Data Flow

**Real-Time (Webhook)**:
```
YouTube publishes video
    → PubSubHubbub notification
    → Webhook receives (8080)
    → Extract metadata
    → Store in MongoDB
    → Available via API
```

**Initial Ingestion**:
```
python ingest_initial.py
    → yt-dlp fetches 1000 videos/channel
    → Build documents
    → Upsert to MongoDB
    → Skip duplicates
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- MongoDB Atlas (cloud database)
- Google API credentials
  - YouTube API key
  - Gemini API key
- A publicly accessible webhook URL (for production)

### 1. Clone and Setup

```bash
git clone https://github.com/AmitC04/Youtube_pipeline_CloudNative
cd youtube-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy env template
cp .env.example .env

# Edit .env with your values:
# - MONGO_URI: Your MongoDB Atlas connection string
# - YOUTUBE_API_KEY: Get from Google Cloud Console
# - GEMINI_API_KEY: Get from Google AI Studio
# - API_KEY: Create a secure random key
# - WEBHOOK_SECRET: Random string for signature verification
# - WEBHOOK_BASE_URL: Your public webhook URL (or http://localhost:8080 for dev)
```

### 3. Initialize Database

```bash
# Perform initial bulk ingestion (1000 videos per channel)
python ingest_initial.py

# Or with custom limit
python ingest_initial.py --limit 500
```

### 4. Subscribe to YouTube Channels

```bash
# Subscribe to real-time notifications
python main.py subscribe
```

### 5. Start Services

**Local Development - All Services Together:**
```bash
# Start webhook + API servers
python main.py all
```

**Individual Services:**
```bash
# Terminal 1: Start webhook server (receives notifications)
python main.py webhook

# Terminal 2: Start REST API server
python main.py api

# Terminal 3: Start Streamlit chatbot
python main.py chatbot
```

---

## 📚 Usage Guide

### Command-Line Interface

#### Query Database

```bash
# Show 10 latest videos
python query_latest.py

# Show 20 latest videos
python query_latest.py --limit 20

# Videos from last 24 hours
python query_latest.py --last-24h

# Videos from specific channel
python query_latest.py --channel Bloomberg

# Search by keyword
python query_latest.py --search "economy"

# Top viewed videos
python query_latest.py --top-viewed

# Database statistics
python query_latest.py --stats
```

#### Initial Ingestion

```bash
# Default: 500 videos per channel
python ingest_initial.py

# Custom limit: 1000 videos per channel
python ingest_initial.py --limit 1000

# Specific channel
python ingest_initial.py --channel https://www.youtube.com/@markets --limit 200
```

#### Subscription Management

```bash
# Subscribe to channels for real-time notifications
python main.py subscribe

# Unsubscribe
python main.py unsubscribe
```

### REST API Usage

#### Using cURL

```bash
# Get latest videos
curl http://localhost:8000/latest?limit=10

# Get videos from last 24 hours
curl http://localhost:8000/last24h

# Get videos from specific channel
curl http://localhost:8000/channel/Bloomberg

# Search videos
curl "http://localhost:8000/search?q=economy&limit=10"

# Get popular videos
curl http://localhost:8000/videos/popular?limit=10&days=7

# List all channels
curl http://localhost:8000/channels/list

# Get database statistics
curl http://localhost:8000/stats

# Get specific video
curl http://localhost:8000/videos/VIDEO_ID_HERE

# Health check
curl http://localhost:8000/health
```

#### Using Postman

1. Import `postman_collection.json` into Postman
2. Update environment variables (`base_url`, `webhook_url`, `api_key`)
3. Run requests directly

#### Using Python

```python
import requests

# Get latest videos
response = requests.get('http://localhost:8000/latest?limit=10')
videos = response.json()['results']

# Search videos
response = requests.get('http://localhost:8000/search', params={
    'q': 'market update',
    'limit': 10
})

# Get by channel
response = requests.get('http://localhost:8000/channel/Bloomberg')
```

### Chatbot Usage

```bash
# Start chatbot
python main.py chatbot

# Open browser to http://localhost:8501
```

**Example Prompts:**
- "How many Bloomberg videos in the database?"
- "Show me videos from last 24 hours"
- "Find videos about USA"
- "What are the trending topics?"
- "Get videos about inflation"
- "List all channels"

---

## 🏗️ Docker Deployment

### Local Development with Docker Compose

```bash
# Start all services (webhook + API + MongoDB)
docker-compose up -d

# View logs
docker-compose logs -f webhook
docker-compose logs -f api

# Stop services
docker-compose down
```

### Build Docker Image

```bash
# Build image
docker build -t youtube-pipeline:latest .

# Run webhook server
docker run -p 8080:8080 \
  -e MONGO_URI="mongodb+srv://..." \
  -e GEMINI_API_KEY="..." \
  youtube-pipeline:latest

# Run API server
docker run -p 8000:8000 \
  -e MONGO_URI="mongodb+srv://..." \
  -e API_KEY="..." \
  youtube-pipeline:latest \
  python main.py api
```

---

## ☁️ Cloud Deployment

### Google Cloud Run

```bash
# 1. Set up Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Deploy using script
cd infra
bash deploy.sh

# 3. Get service URLs from output
# Webhook: https://youtube-pipeline-webhook-xxx.run.app
# API: https://youtube-pipeline-api-xxx.run.app
```

### Environment Variables on Cloud Run

```bash
# Update webhook service
gcloud run services update youtube-pipeline-webhook \
  --set-env-vars=MONGO_URI={your_mongo_uri},GEMINI_API_KEY={key}

# Update API service
gcloud run services update youtube-pipeline-api \
  --set-env-vars=MONGO_URI={your_mongo_uri},API_KEY={key}
```

### Cloudflare Workers (Serverless)

```bash
# Create Cloudflare Worker
wrangler init youtube-pipeline

# Deploy
wrangler deploy
```

### Render

```bash
# Push to GitHub
git push origin main

# Connect Render to GitHub repository
# - Select this repository
# - Set build command: pip install -r requirements.txt
# - Set start command: gunicorn webhook.webhook_app:app
```

---

## 🔌 Webhook Configuration

### How It Works

1. **Subscribe** to YouTube channels via PubSubHubbub hub
2. YouTube publishes **Atom feed** to our webhook on new videos
3. Webhook **verifies** subscription and processes feed
4. Extract **metadata** from feed (title, channel, date, etc.)
5. **Fetch full details** using yt-dlp
6. **Store in MongoDB** with deduplication

### Webhook Verification (Hub Challenge)

When PubSubHubbub initiates subscription, it sends:
```
GET /webhook?hub.mode=subscribe&hub.challenge=CHALLENGE_STRING&...
```

Our endpoint responds with **plain text challenge** (required by spec):
```
CHALLENGE_STRING
```

### Webhook Signature Verification

For production, PubSubHubbub signs requests:
```
X-Hub-Signature: sha1=HMAC_SIGNATURE
```

We verify using `WEBHOOK_SECRET`:
```python
expected = hmac.new(secret.encode(), body, hashlib.sha1).hexdigest()
assert hmac.compare_digest(signature, expected)
```

---

## 📊 Database Schema

### Videos Collection

```json
{
  "_id": ObjectId,
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "upload_date": "2024-02-21T12:00:00Z",
  "view_count": 1000000,
  "like_count": 50000,
  "comment_count": 1000,
  "description": "Video description...",
  "channel_id": "UCIALMKvObZNtJ6AmdCLP7Lg",
  "channel": "Bloomberg Markets",
  "channel_url": "https://www.youtube.com/c/BloombergMarkets",
  "duration": 600,
  "thumbnail": "https://i.ytimg.com/vi/...",
  "tags": ["finance", "market", "bitcoin"],
  "ingested_at": "2024-02-21T12:30:00Z",
  "source": "pubsubhubbub"
}
```

### Indexes

- **Unique**: `video_id` (no duplicates)
- **Descending**: `upload_date` (recent videos)
- **Ascending**: `channel_id` (by channel)
- **Text**: `title`, `description` (search)

---

## 🔐 Security

### API Authentication

All endpoints require Bearer token (except health check):
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/videos/recent
```

### Webhook Signature Verification

Enabled in production:
```python
if expected_signature:
    verify_hmac_signature(request_body, expected_signature)
```

### Environment Variable Security

Keep sensitive data in `.env`:
```bash
# .env (never commit to Git)
MONGO_URI=mongodb+srv://admin:password@...
API_KEY=your-secure-key-here
WEBHOOK_SECRET=your-webhook-secret
```

### Network Security

- Use HTTPS in production
- Configure Cloud Run to allow only authenticated access
- Add CORS headers as needed
- Rate limiting on API endpoints

---

## 📈 Performance & Monitoring

### Logging

All components log to stdout with timestamps:
```
2024-02-21 12:30:45 - webhook - INFO - Received webhook POST request
2024-02-21 12:30:46 - database - INFO - Inserted video: dQw4w9WgXcQ
```

### Health Checks

Built-in health endpoints:
- Webhook: `GET http://localhost:8080/health`
- API: `GET http://localhost:8000/health`
- Checks database connectivity

### Database Monitoring

```bash
# Check video count
python query_latest.py --stats

# Monitor ingestion progress
python main.py query --last-24h

# Track by channel
python query_latest.py --channel Bloomberg
```

### Cloud Monitoring (GCP)

```bash
# View Cloud Run logs
gcloud run logs read youtube-pipeline-webhook --region=asia-south1

# Monitor metrics
# - Request rate
# - Latency
# - Error rate
# - Memory usage
```

---

## 🐛 Troubleshooting

### MongoDB Connection Issues

```bash
# Test connection
python -c "from db import get_db; db = get_db(); print(list(db.list_collection_names()))"

# Verify MONGO_URI format:
# mongodb+srv://username:password@cluster0.xxx.mongodb.net/database?retryWrites=true
```

### Webhook Not Receiving Notifications

1. Check subscription status:
   ```bash
   python main.py query --stats  # Should show recent videos
   ```

2. Verify webhook URL is publicly accessible:
   ```bash
   curl https://your-webhook-url/webhook?hub.mode=subscribe&hub.challenge=test_challenge
   ```

3. Check logs:
   ```bash
   # See incoming webhook requests
   docker-compose logs -f webhook
   ```

4. Re-subscribe to channels:
   ```bash
   python main.py unsubscribe
   python main.py subscribe
   ```

### API Errors

```
403 Unauthorized: Check API_KEY in .env
500 Database Error: Verify MONGO_URI and network access
404 Not Found: Video doesn't exist in database
```

### Chatbot Issues

```bash
# Verify Streamlit installation
pip list | grep streamlit

# Check Gemini API key
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY')"

# Run with debug
streamlit run chatbot/app.py --logger.level=debug
```

---

## 📋 Project Structure

```
youtube-pipeline/
├── main.py                      # CLI entrypoint
├── db.py                        # MongoDB configuration
├── query_db.py                  # Database queries
├── ingest_initial.py            # Bulk ingestion script
├── query_latest.py              # Query CLI tool
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── Dockerfile                   # Container image
├── docker-compose.yml           # Multi-container setup
├── postman_collection.json      # API testing
│
├── api/
│   ├── __init__.py
│   └── api.py                   # FastAPI endpoints
│
├── webhook/
│   ├── __init__.py
│   ├── webhook_app.py           # PubSubHubbub receiver
│   └── subscribe.py             # Channel subscription manager
│
├── chatbot/
│   ├── __init__.py
│   ├── app.py                   # Streamlit UI
│   └── agents.py                # AI agent with tools
│
├── ingestion/
│   ├── __init__.py
│   ├── bulk_ingest.py           # yt-dlp video fetcher
│   ├── get_channel_ids.py       # Channel ID helper
│   └── subscribe.py             # Subscription manager
│
├── infra/
│   └── deploy.sh                # Google Cloud Run script
│
└── README.md                    # This file
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- [YouTube Data API](https://developers.google.com/youtube/v3)
- [PubSubHubbub](https://www.w3.org/TR/websub/) (WebSub)
- [MongoDB Atlas](https://www.mongodb.com/atlas)
- [Google Generative AI](https://ai.google/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

---

## 📧 Support

For issues, questions, or suggestions:
1. Check existing [GitHub Issues](https://github.com/AmitC04/Youtube_pipeline_CloudNative/issues)
2. Create a new issue with detailed description
3. Include logs and environment information

---

## 🎯 Assessment Requirements Met

✅ **Real-time webhook ingestion** - PubSubHubbub integration
✅ **Zero polling** - Event-driven architecture  
✅ **Cloud database** - MongoDB Atlas with proper schema
✅ **1000+ videos** - Initial bulk ingestion via yt-dlp
✅ **REST API** - Complete endpoint coverage
✅ **Serverless deployment** - Google Cloud Run ready
✅ **AI Chatbot** - Google Generative AI with tool use
✅ **Full documentation** - Architecture, setup, usage
✅ **Error handling** - Comprehensive logging everywhere
✅ **Production ready** - Docker, secrets, security

---

**Last Updated**: February 2024  
**Version**: 1.0.0  
**Status**: Production Ready ✅
