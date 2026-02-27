"""
db.py - MongoDB connection and schema utilities.
Uses the MONGO_URI from .env to connect to MongoDB Atlas.
Falls back to local store when Atlas is unavailable.
"""
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

MONGO_URI     = os.environ.get("MONGO_URI", "")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "youtube_pipeline")

_client          = None
_indexes_created = False
_use_local       = False   # set True after first failed Atlas attempt


def _try_mongo():
    global _client
    if not MONGO_URI:
        return None
    try:
        from pymongo import MongoClient
        c = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=4000,
            connectTimeoutMS=4000,
            socketTimeoutMS=10000,
            maxPoolSize=10,
        )
        c[MONGO_DB_NAME].command("ping")
        _client = c
        logger.info("✅ MongoDB Atlas connected")
        return _client[MONGO_DB_NAME]
    except Exception as e:
        logger.warning(f"MongoDB unavailable, switching to local store: {e}")
        return None


def get_db():
    global _client, _use_local
    if _use_local:
        return None
    if _client is not None:
        return _client[MONGO_DB_NAME]
    db = _try_mongo()
    if db is None:
        _use_local = True
    return db


def get_videos_collection(ensure_indexes: bool = False):
    global _indexes_created, _use_local
    db = get_db()
    if _use_local or db is None:
        from assets._data import get_local_collection
        return get_local_collection()
    col = db["videos"]
    if ensure_indexes and not _indexes_created:
        _create_indexes(col)
    return col


def _create_indexes(col):
    global _indexes_created
    try:
        col.create_index([("video_id", 1)], unique=True, background=True)
        col.create_index([("upload_date", -1)], background=True)
        col.create_index([("channel_id", 1)], background=True)
        col.create_index(
            [("title", "text"), ("description", "text")],
            background=True,
            name="text_search_index"
        )
        _indexes_created = True
        logger.info("✅ Database indexes created")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")


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
        "video_id":      video_id,
        "title":         raw.get("title", ""),
        "url":           raw.get("url") or f"https://www.youtube.com/watch?v={video_id}",
        "upload_date":   upload_date_iso,
        "view_count":    int(raw.get("view_count") or 0),
        "like_count":    int(raw.get("like_count") or 0),
        "description":   raw.get("description", "")[:2000],
        "channel_id":    raw.get("channel_id", ""),
        "channel":       raw.get("channel") or raw.get("uploader", ""),
        "channel_url":   raw.get("channel_url") or raw.get("uploader_url", ""),
        "duration":      raw.get("duration", 0),
        "thumbnail":     raw.get("thumbnail", ""),
        "tags":          raw.get("tags", []),
        "comment_count": int(raw.get("comment_count") or 0),
        "ingested_at":   datetime.utcnow().isoformat() + "Z",
        "source":        raw.get("_source", "yt-dlp"),
    }
    return doc


def upsert_video(doc: dict) -> bool:
    col = get_videos_collection()
    if hasattr(col, 'update_one'):
        result = col.update_one(
            {"video_id": doc["video_id"]},
            {"$set": doc},
            upsert=True
        )
        return result.upserted_id is not None
    # local store — no-op for demo
    return False
