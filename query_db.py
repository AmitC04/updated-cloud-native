"""
query_db.py
Utility functions for querying the video database with various filters and aggregations
"""
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from db import get_videos_collection


def search_videos(text_query: str = None, 
                 channel: str = None, 
                 min_views: int = None, 
                 max_views: int = None,
                 date_from: str = None,
                 date_to: str = None,
                 limit: int = 50,
                 offset: int = 0) -> List[Dict]:
    """
    Advanced search function for videos with multiple filter options
    """
    collection = get_videos_collection()
    
    query_filter = {}
    
    # Text search in title and description
    if text_query:
        query_filter["$text"] = {"$search": text_query}
    
    # Channel filter
    if channel:
        query_filter["channel"] = {"$regex": channel, "$options": "i"}
    
    # View count filters
    if min_views is not None or max_views is not None:
        view_filter = {}
        if min_views is not None:
            view_filter["$gte"] = min_views
        if max_views is not None:
            view_filter["$lte"] = max_views
        if view_filter:
            query_filter["view_count"] = view_filter
    
    # Date range filter
    if date_from or date_to:
        date_filter = {}
        if date_from:
            date_filter["$gte"] = date_from
        if date_to:
            date_filter["$lte"] = date_to
        if date_filter:
            query_filter["upload_date"] = date_filter
    
    # Execute query with sorting and pagination
    cursor = collection.find(query_filter).sort("upload_date", -1).skip(offset).limit(limit)
    results = list(cursor)
    
    # Clean up results
    for result in results:
        if "_id" in result:
            del result["_id"]
    
    return results


def get_videos_by_channel(channel: str, limit: int = 50) -> List[Dict]:
    """
    Get videos from a specific channel
    """
    collection = get_videos_collection()
    
    query_filter = {"channel": {"$regex": channel, "$options": "i"}}
    
    cursor = collection.find(query_filter).sort("upload_date", -1).limit(limit)
    results = list(cursor)
    
    for result in results:
        if "_id" in result:
            del result["_id"]
    
    return results


def get_top_videos(sort_by: str = "view_count", limit: int = 20) -> List[Dict]:
    """
    Get top videos based on specified metric
    """
    collection = get_videos_collection()
    
    sort_direction = -1  # Descending order
    cursor = collection.find({}).sort(sort_by, sort_direction).limit(limit)
    results = list(cursor)
    
    for result in results:
        if "_id" in result:
            del result["_id"]
    
    return results


def get_video_statistics() -> Dict:
    """
    Get comprehensive statistics about the video database
    """
    collection = get_videos_collection()
    
    total_videos = collection.count_documents({})
    total_channels = len(collection.distinct("channel"))
    
    # Get stats for each channel
    channel_stats = list(collection.aggregate([
        {
            "$group": {
                "_id": "$channel",
                "video_count": {"$sum": 1},
                "total_views": {"$sum": "$view_count"},
                "avg_views": {"$avg": "$view_count"},
                "total_likes": {"$sum": "$like_count"},
                "avg_likes": {"$avg": "$like_count"},
                "latest_video": {"$max": "$upload_date"}
            }
        },
        {
            "$project": {
                "channel": "$_id",
                "video_count": 1,
                "total_views": 1,
                "avg_views": {"$round": ["$avg_views", 2]},
                "total_likes": 1,
                "avg_likes": {"$round": ["$avg_likes", 2]},
                "latest_video": 1,
                "_id": 0
            }
        },
        {
            "$sort": {"avg_views": -1}
        }
    ]))
    
    # Get overall platform stats
    platform_stats = list(collection.aggregate([
        {
            "$group": {
                "_id": None,
                "total_views": {"$sum": "$view_count"},
                "total_likes": {"$sum": "$like_count"},
                "avg_duration": {"$avg": "$duration"},
                "earliest_video": {"$min": "$upload_date"},
                "latest_video": {"$max": "$upload_date"}
            }
        },
        {
            "$project": {
                "total_views": 1,
                "total_likes": 1,
                "avg_duration": {"$round": ["$avg_duration", 2]},
                "earliest_video": 1,
                "latest_video": 1,
                "_id": 0
            }
        }
    ]))
    
    overall_stats = platform_stats[0] if platform_stats else {}
    
    return {
        "database": {
            "total_videos": total_videos,
            "total_channels": total_channels
        },
        "channels": channel_stats,
        "overall": overall_stats
    }


def get_trending_videos(days: int = 7, limit: int = 20) -> List[Dict]:
    """
    Get trending videos based on recent activity (views, likes, comments)
    """
    collection = get_videos_collection()
    
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    cutoff_iso = cutoff_date.isoformat()
    
    # Query for recent videos with high engagement
    query_filter = {
        "upload_date": {"$gte": cutoff_iso}
    }
    
    # Sort by a combination of views, likes, and comments
    cursor = collection.find(query_filter).sort([
        ("view_count", -1),
        ("like_count", -1),
        ("comment_count", -1)
    ]).limit(limit)
    
    results = list(cursor)
    
    for result in results:
        if "_id" in result:
            del result["_id"]
    
    return results


def get_videos_by_date_range(date_from, date_to, limit: int = 50, channel: str = None) -> List[Dict]:
    """
    Get videos within a specific date range
    date_from and date_to can be datetime objects or ISO format strings
    """
    collection = get_videos_collection()
    
    # Convert datetime objects to ISO format strings if needed
    if isinstance(date_from, datetime):
        date_from = date_from.isoformat()
    if isinstance(date_to, datetime):
        date_to = date_to.isoformat()
    
    query_filter = {
        "upload_date": {
            "$gte": date_from,
            "$lte": date_to
        }
    }
    
    # Add channel filter if specified
    if channel:
        query_filter["channel"] = {"$regex": channel, "$options": "i"}
    
    cursor = collection.find(query_filter).sort("upload_date", -1).limit(limit)
    results = list(cursor)
    
    for result in results:
        if "_id" in result:
            del result["_id"]
    
    return results


def get_most_recent_entries(limit: int = 10) -> List[Dict]:
    """
    Return the most recent entries added to the collection
    This function is specifically for the assessment to test webhook and ingestion
    """
    collection = get_videos_collection()
    
    # Query for most recent entries based on upload_date
    cursor = collection.find({}).sort("upload_date", -1).limit(limit)
    results = list(cursor)
    
    for result in results:
        if "_id" in result:
            del result["_id"]
    
    return results


def get_recent_videos(limit: int = 10, channel: str = None) -> List[Dict]:
    """Get recently published videos, optionally filtered by channel"""
    collection = get_videos_collection()
    
    query_filter = {}
    if channel:
        query_filter["channel"] = {"$regex": channel, "$options": "i"}
    
    cursor = collection.find(query_filter).sort("upload_date", -1).limit(limit)
    results = list(cursor)
    
    for result in results:
        if "_id" in result:
            del result["_id"]
    
    return results


def count_videos_by_channel(channel: str) -> int:
    """Count total videos from a specific channel"""
    collection = get_videos_collection()
    
    query_filter = {"channel": {"$regex": channel, "$options": "i"}}
    return collection.count_documents(query_filter)


def get_channel_stats() -> Dict:
    """Get statistics for each channel"""
    collection = get_videos_collection()
    
    stats = {}
    channels = collection.distinct("channel")
    
    for channel in channels:
        count = collection.count_documents({"channel": channel})
        stats[channel] = count
    
    return stats


def get_videos_last_24h(channel: str = None) -> List[Dict]:
    """Get videos published in the last 24 hours"""
    start_time = datetime.utcnow() - timedelta(hours=24)
    return get_videos_by_date_range(start_time, datetime.utcnow(), limit=50, channel=channel)
