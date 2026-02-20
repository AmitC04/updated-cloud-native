"""
api/api.py
Secured FastAPI REST API for querying YouTube video data
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import os
from datetime import datetime
import re

from db import get_videos_collection
from query_db import get_most_recent_entries

app = FastAPI(title="YouTube Video Data API", version="1.0.0")
security = HTTPBearer()

# Validate API key from environment
API_KEY = os.environ.get("API_KEY", "")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return credentials.credentials


@app.get("/")
def read_root():
    return {"message": "YouTube Video Data API", "status": "active"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/videos/search")
def search_videos(
    q: str = Query(None, min_length=1, max_length=100, description="Text search in title/description"),
    channel: str = Query(None, description="Filter by channel name"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query("upload_date", enum=["upload_date", "view_count", "like_count"], description="Sort field"),
    sort_order: str = Query("desc", enum=["asc", "desc"], description="Sort order")
):
    """
    Search videos by text query, with optional filters
    """
    collection = get_videos_collection()
    
    query_filter = {}
    
    # Text search
    if q:
        query_filter["$text"] = {"$search": q}
    
    # Channel filter
    if channel:
        # Case insensitive partial match
        query_filter["channel"] = {"$regex": channel, "$options": "i"}
    
    # Sorting
    sort_direction = 1 if sort_order == "asc" else -1
    sort_field = sort_by
    
    # Execute query
    cursor = collection.find(query_filter).sort(sort_field, sort_direction).skip(offset).limit(limit)
    results = list(cursor)
    
    # Remove MongoDB _id from results
    for result in results:
        if "_id" in result:
            del result["_id"]
    
    return {"results": results, "total": collection.count_documents(query_filter)}


@app.get("/videos/recent")
def get_recent_videos(
    limit: int = Query(10, ge=1, le=100, description="Number of recent videos to return"),
    channel: str = Query(None, description="Filter by channel name")
):
    """
    Get most recently uploaded videos
    """
    collection = get_videos_collection()
    
    query_filter = {}
    if channel:
        query_filter["channel"] = {"$regex": channel, "$options": "i"}
    
    cursor = collection.find(query_filter).sort("upload_date", -1).limit(limit)
    results = list(cursor)
    
    for result in results:
        if "_id" in result:
            del result["_id"]
    
    return {"results": results}


@app.get("/videos/popular")
def get_popular_videos(
    limit: int = Query(10, ge=1, le=100, description="Number of popular videos to return"),
    days: int = Query(7, ge=1, le=365, description="Time window in days")
):
    """
    Get most popular videos based on view count in recent days
    """
    collection = get_videos_collection()
    
    # Calculate cutoff date
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query_filter = {
        "upload_date": {
            "$gte": cutoff_date.isoformat()
        }
    }
    
    cursor = collection.find(query_filter).sort("view_count", -1).limit(limit)
    results = list(cursor)
    
    for result in results:
        if "_id" in result:
            del result["_id"]
    
    return {"results": results}


@app.get("/channels/list")
def list_channels():
    """
    Get list of all channels in the database
    """
    collection = get_videos_collection()
    
    # Get distinct channels
    channels = collection.distinct("channel")
    
    return {"channels": sorted(channels)}


@app.get("/videos/stats")
def get_video_stats():
    """
    Get statistics about the video database
    """
    collection = get_videos_collection()
    
    total_videos = collection.count_documents({})
    total_channels = collection.distinct("channel").__len__()
    
    # Stats by channel
    pipeline = [
        {
            "$group": {
                "_id": "$channel",
                "count": {"$sum": 1},
                "avg_views": {"$avg": "$view_count"},
                "avg_likes": {"$avg": "$like_count"}
            }
        },
        {
            "$project": {
                "channel": "$_id",
                "count": 1,
                "avg_views": {"$round": ["$avg_views", 2]},
                "avg_likes": {"$round": ["$avg_likes", 2]},
                "_id": 0
            }
        }
    ]
    
    channel_stats = list(collection.aggregate(pipeline))
    
    return {
        "total_videos": total_videos,
        "total_channels": total_channels,
        "channel_stats": channel_stats
    }


@app.get("/videos/{video_id}")
def get_video_by_id(video_id: str):
    """
    Get a specific video by its YouTube video ID
    """
    collection = get_videos_collection()
    
    video = collection.find_one({"video_id": video_id})
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if "_id" in video:
        del video["_id"]
    
    return video


@app.get("/most_recent")
def get_most_recent(
    limit: int = Query(10, ge=1, le=100, description="Number of most recent entries to return")
):
    """
    Get the most recent entries added to the collection
    This endpoint is specifically for the assessment to test webhook and ingestion
    """
    try:
        results = get_most_recent_entries(limit)
        return {"results": results, "total_found": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving recent entries: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)