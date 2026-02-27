"""
ingestion/bulk_ingest.py
Downloads last 1000 videos metadata from target YouTube channels using yt-dlp.
Usage: python ingestion/bulk_ingest.py
       python ingestion/bulk_ingest.py --limit 50
       python ingestion/bulk_ingest.py --channel https://www.youtube.com/@markets --limit 100
"""
import sys
import os
import time
import argparse
import logging
import yt_dlp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db import build_video_doc, upsert_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

TARGET_CHANNELS = [
    "https://www.youtube.com/@markets",
    "https://www.youtube.com/@ANINewsIndia",
    # Add more high-frequency channels as needed
]
DEFAULT_LIMIT = 1000


def fetch_video_ids(channel_url: str, limit: int) -> list:
    log.info(f"Fetching up to {limit} video IDs from: {channel_url}")
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "playlistend": limit,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"{channel_url}/videos", download=False)
        if not info or "entries" not in info:
            return []
        entries = [e for e in info["entries"] if e and e.get("id")]
        log.info(f"Found {len(entries)} video IDs")
        return [e["id"] for e in entries]


def fetch_full_metadata(video_id: str) -> dict | None:
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {"quiet": True, "ignoreerrors": True, "no_warnings": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        log.warning(f"Failed to fetch metadata for {video_id}: {e}")
        return None


def ingest_channel(channel_url: str, limit: int = DEFAULT_LIMIT):
    log.info(f"=== Starting ingestion for: {channel_url} ===")
    video_ids = fetch_video_ids(channel_url, limit)
    if not video_ids:
        log.error("No videos found. Skipping.")
        return 0, 0, 0

    inserted = updated = failed = 0
    for i, vid_id in enumerate(video_ids, 1):
        log.info(f"[{i}/{len(video_ids)}] Processing: {vid_id}")
        raw = fetch_full_metadata(vid_id)
        if not raw:
            failed += 1
            continue
        raw["_source"] = "yt-dlp"
        doc = build_video_doc(raw)
        try:
            is_new = upsert_video(doc)
            if is_new:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            log.error(f"DB error for {vid_id}: {e}")
            failed += 1
        time.sleep(2) if i % 10 == 0 else time.sleep(0.5)

    log.info(f"=== Done | Inserted: {inserted} | Updated: {updated} | Failed: {failed} ===")
    return inserted, updated, failed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", type=str, default=None)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()
    channels = [args.channel] if args.channel else TARGET_CHANNELS
    for channel_url in channels:
        ingest_channel(channel_url, args.limit)


if __name__ == "__main__":
    main()