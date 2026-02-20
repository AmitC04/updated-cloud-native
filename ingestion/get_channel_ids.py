"""
ingestion/get_channel_ids.py
Run this once to get channel IDs. Output: CHANNEL_IDS=UC...,UC...
Usage: python ingestion/get_channel_ids.py
"""
import sys
import os
import yt_dlp

TARGET_CHANNELS = [
    ("Bloomberg Markets", "https://www.youtube.com/@markets"),
    ("ANI News India", "https://www.youtube.com/@ANINewsIndia"),
    # Add more high-frequency channels as needed
]


def get_channel_id(channel_url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "playlist_items": "1",
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"{channel_url}/videos", download=False)
        return {
            "channel_id": info.get("channel_id") or info.get("uploader_id", ""),
            "channel": info.get("channel") or info.get("uploader", ""),
            "channel_url": info.get("channel_url") or info.get("uploader_url", ""),
        }


def main():
    print("Resolving YouTube Channel IDs...\n")
    channel_ids = []
    for name, url in TARGET_CHANNELS:
        print(f"Fetching: {name} ({url})")
        try:
            info = get_channel_id(url)
            cid = info["channel_id"]
            print(f"  Channel ID: {cid}")
            print(f"  Name: {info['channel']}\n")
            channel_ids.append(cid)
        except Exception as e:
            print(f"  Error: {e}\n")
    print("=== Copy this line into your .env file ===")
    print(f"CHANNEL_IDS={','.join(channel_ids)}")


if __name__ == "__main__":
    main()