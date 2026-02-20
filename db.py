"""
db.py - Shared MongoDB connection and schema utilities
"""
import os
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI", "")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "youtube_pipeline")


def get_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    return client[MONGO_DB_NAME]


def get_videos_collection() -> Collection:
    db = get_db()
    col = db["videos"]
    col.create_index([("video_id", ASCENDING)], unique=True, background=True)
    col.create_index([("upload_date", DESCENDING)], background=True)
    col.create_index([("channel_id", ASCENDING)], background=True)
    col.create_index(
        [("title", "text"), ("description", "text")],
        background=True,
        name="text_search_index"
    )
    return col


def build_video_doc(raw: dict) -> dict:
    upload_date_raw = raw.get("upload_date", "")
    if upload_date_raw and len(upload_date_raw) == 8:
        try:
            dt = datetime.strptime(upload_date_raw, "%Y%m%d")
            upload_date_iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            upload_date_iso = upload_date_raw
    else:
        upload_date_iso = upload_date_raw

    video_id = raw.get("video_id") or raw.get("id", "")
    doc = {
        "video_id": video_id,
        "title": raw.get("title", ""),
        "url": raw.get("url") or f"https://www.youtube.com/watch?v={video_id}",
        "upload_date": upload_date_iso,
        "view_count": int(raw.get("view_count") or 0),
        "like_count": int(raw.get("like_count") or 0),
        "description": raw.get("description", "")[:2000],
        "channel_id": raw.get("channel_id", ""),
        "channel": raw.get("channel") or raw.get("uploader", ""),
        "channel_url": raw.get("channel_url") or raw.get("uploader_url", ""),
        "duration": raw.get("duration", 0),
        "thumbnail": raw.get("thumbnail", ""),
        "tags": raw.get("tags", []),
        "comment_count": int(raw.get("comment_count") or 0),
        "ingested_at": datetime.utcnow().isoformat() + "Z",
        "source": raw.get("_source", "yt-dlp"),
    }
    return doc


def upsert_video(doc: dict) -> bool:
    col = get_videos_collection()
    result = col.update_one(
        {"video_id": doc["video_id"]},
        {"$set": doc},
        upsert=True
    )
    return result.upserted_id is not None