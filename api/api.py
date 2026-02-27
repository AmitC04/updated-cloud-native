"""
api/api.py
Secured FastAPI REST API for querying YouTube video data.
Provides endpoints for searching, filtering, and analyzing video metadata.
"""
import os
import logging
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime, timedelta

from db import get_videos_collection
from query_db import get_most_recent_entries, search_videos, get_videos_by_channel, get_top_videos

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Video Data API",
    description="Cloud-native API for querying real-time YouTube video metadata",
    version="1.0.0"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
API_KEY = os.environ.get("API_KEY", "")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key from Authorization header"""
    if credentials.credentials != API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return credentials.credentials


@app.get("/")
def read_root():
    """Root endpoint with API information"""
    logger.info("Root endpoint accessed")
    return {
        "service": "YouTube Video Data API",
        "status": "active",
        "version": "1.0.0",
        "docs_url": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring"""
    try:
        collection = get_videos_collection()
        collection.count_documents({})
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")


@app.get("/latest")
def get_latest_videos(
    limit: int = Query(10, ge=1, le=100, description="Number of videos to return")
):
    """
    Get the latest uploaded videos (most recent)
    """
    try:
        logger.info(f"Fetching {limit} latest videos")
        collection = get_videos_collection()
        
        videos = list(collection.find({}).sort("upload_date", -1).limit(limit))
        
        for video in videos:
            video.pop("_id", None)
        
        return {"results": videos, "total": len(videos)}
    except Exception as e:
        logger.error(f"Error fetching latest videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/last24h")
def get_last_24h_videos(
    channel: Optional[str] = Query(None, description="Optional channel filter"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get videos published in the last 24 hours
    """
    try:
        logger.info(f"Fetching videos from last 24h (channel: {channel})")
        collection = get_videos_collection()
        
        time_24h_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        query_filter = {"upload_date": {"$gte": time_24h_ago}}
        if channel:
            query_filter["channel"] = {"$regex": channel, "$options": "i"}
        
        videos = list(collection.find(query_filter).sort("upload_date", -1).limit(limit))
        
        for video in videos:
            video.pop("_id", None)
        
        return {"results": videos, "total": len(videos)}
    except Exception as e:
        logger.error(f"Error fetching 24h videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/channel/{channel_name}")
def get_channel_videos(
    channel_name: str,
    limit: int = Query(20, ge=1, le=100, description="Number of videos to return"),
    sort_by: str = Query("upload_date", enum=["upload_date", "view_count", "like_count"])
):
    """
    Get videos from a specific channel
    """
    try:
        logger.info(f"Fetching videos for channel: {channel_name}")
        collection = get_videos_collection()
        
        sort_direction = -1 if sort_by == "upload_date" else -1
        query_filter = {"channel": {"$regex": channel_name, "$options": "i"}}
        
        videos = list(collection.find(query_filter).sort(sort_by, sort_direction).limit(limit))
        
        if not videos:
            logger.warning(f"No videos found for channel: {channel_name}")
            raise HTTPException(status_code=404, detail=f"No videos found for channel: {channel_name}")
        
        for video in videos:
            video.pop("_id", None)
        
        channel_display = videos[0]["channel"] if videos else channel_name
        return {
            "channel": channel_display,
            "results": videos,
            "total": len(videos)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching channel videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
def search_videos_endpoint(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    channel: Optional[str] = Query(None, description="Optional channel filter"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("upload_date", enum=["upload_date", "view_count", "like_count"])
):
    """
    Search videos by text query in title and description
    """
    try:
        logger.info(f"Searching for: {q}")
        collection = get_videos_collection()
        
        query_filter = {}
        
        # Text search
        if q:
            query_filter["$text"] = {"$search": q}
        
        # Channel filter
        if channel:
            query_filter["channel"] = {"$regex": channel, "$options": "i"}
        
        sort_direction = -1
        
        # Execute query
        cursor = collection.find(query_filter).sort(sort_by, sort_direction).skip(offset).limit(limit)
        results = list(cursor)
        total = collection.count_documents(query_filter)
        
        for result in results:
            result.pop("_id", None)
        
        logger.info(f"Search found {total} results for: {q}")
        return {"query": q, "results": results, "total": total, "offset": offset}
    except Exception as e:
        logger.error(f"Error searching videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/popular")
def get_popular_videos(
    limit: int = Query(10, ge=1, le=100, description="Number of popular videos to return"),
    days: int = Query(7, ge=1, le=365, description="Time window in days")
):
    """
    Get most popular videos based on view count in recent days
    """
    try:
        logger.info(f"Fetching popular videos (last {days} days)")
        collection = get_videos_collection()
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query_filter = {"upload_date": {"$gte": cutoff_date}}
        
        videos = list(collection.find(query_filter).sort("view_count", -1).limit(limit))
        
        for video in videos:
            video.pop("_id", None)
        
        return {"results": videos, "total": len(videos)}
    except Exception as e:
        logger.error(f"Error fetching popular videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/channels/list")
def list_channels():
    """
    Get list of all channels in the database with statistics
    """
    try:
        logger.info("Listing all channels")
        collection = get_videos_collection()
        
        # Get distinct channels with count
        pipeline = [
            {
                "$group": {
                    "_id": "$channel",
                    "count": {"$sum": 1},
                    "avg_views": {"$avg": "$view_count"}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$project": {
                    "channel": "$_id",
                    "video_count": "$count",
                    "avg_views": {"$round": ["$avg_views", 0]},
                    "_id": 0
                }
            }
        ]
        
        channels = list(collection.aggregate(pipeline))
        
        return {
            "total_channels": len(channels),
            "channels": channels
        }
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats():
    """
    Get overall database statistics
    """
    try:
        logger.info("Fetching database statistics")
        collection = get_videos_collection()
        
        total_videos = collection.count_documents({})
        channels = collection.distinct("channel")
        
        # Detailed stats
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_videos": {"$sum": 1},
                    "total_views": {"$sum": "$view_count"},
                    "total_likes": {"$sum": "$like_count"},
                    "avg_views": {"$avg": "$view_count"},
                    "avg_likes": {"$avg": "$like_count"},
                    "max_views": {"$max": "$view_count"}
                }
            }
        ]
        
        stats = list(collection.aggregate(pipeline))
        stats_data = stats[0] if stats else {}
        
        return {
            "total_videos": total_videos,
            "total_channels": len(channels),
            "stats": {
                "total_views": stats_data.get("total_views", 0),
                "total_likes": stats_data.get("total_likes", 0),
                "avg_views_per_video": round(stats_data.get("avg_views", 0), 2),
                "avg_likes_per_video": round(stats_data.get("avg_likes", 0), 2),
                "most_viewed_video_views": stats_data.get("max_views", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos/{video_id}")
def get_video_by_id(video_id: str):
    """
    Get a specific video by its YouTube video ID
    """
    try:
        logger.info(f"Fetching video: {video_id}")
        collection = get_videos_collection()
        
        video = collection.find_one({"video_id": video_id})
        
        if not video:
            logger.warning(f"Video not found: {video_id}")
            raise HTTPException(status_code=404, detail="Video not found")
        
        video.pop("_id", None)
        
        return video
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook")
async def webhook_endpoint():
    """
    Webhook endpoint for receiving real-time YouTube video notifications.
    This endpoint handles PubSubHubbub notifications from the webhook server.
    """
    logger.info("Webhook endpoint called")
    return {
        "status": "webhook_active",
        "note": "This endpoint is served by webhook server, not API server"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)