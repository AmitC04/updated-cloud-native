"""
ingestion/subscribe.py
Subscribes YouTube channels to PubSubHubbub for real-time push notifications.
Usage: python ingestion/subscribe.py
       python ingestion/subscribe.py --mode unsubscribe
"""
import sys
import os
import argparse
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PUBSUB_HUB_URL = os.environ.get("PUBSUB_HUB_URL", "https://pubsubhubbub.appspot.com/subscribe")
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL", "http://localhost:8080")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
LEASE_SECONDS = 864000

TARGET_CHANNEL_IDS = [
    id_.strip()
    for id_ in os.environ.get("CHANNEL_IDS", "").split(",")
    if id_.strip()
]


def subscribe_channel(channel_id: str, mode: str = "subscribe") -> bool:
    topic_url = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"
    callback_url = f"{WEBHOOK_BASE_URL}/webhook"
    payload = {
        "hub.callback": callback_url,
        "hub.mode": mode,
        "hub.topic": topic_url,
        "hub.verify": "async",
        "hub.secret": WEBHOOK_SECRET,
        "hub.lease_seconds": LEASE_SECONDS,
    }
    log.info(f"[{mode.upper()}] Channel: {channel_id} → Callback: {callback_url}")
    try:
        resp = requests.post(PUBSUB_HUB_URL, data=payload, timeout=30)
        if resp.status_code in (202, 204):
            log.info(f"✓ Success: {mode} request sent for channel {channel_id}")
            return True
        else:
            log.error(f"✗ Failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        log.error(f"✗ Error sending {mode} request for {channel_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["subscribe", "unsubscribe"], default="subscribe")
    args = parser.parse_args()
    
    if not TARGET_CHANNEL_IDS:
        log.error("No CHANNEL_IDS found in environment. Please set CHANNEL_IDS in .env")
        return
    
    if args.mode == "subscribe":
        log.info(f"Subscribing to {len(TARGET_CHANNEL_IDS)} channels...")
    else:
        log.info(f"Unsubscribing from {len(TARGET_CHANNEL_IDS)} channels...")
    
    successes = 0
    for channel_id in TARGET_CHANNEL_IDS:
        if subscribe_channel(channel_id, args.mode):
            successes += 1
    
    log.info(f"Completed: {successes}/{len(TARGET_CHANNEL_IDS)} channels {'subscribed' if args.mode == 'subscribe' else 'unsubscribed'}")


if __name__ == "__main__":
    main()