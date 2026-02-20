"""
scheduler/resubscribe.py
Regularly resubscribes to YouTube channels to maintain PubSubHubbub subscriptions
Designed to run periodically (e.g., daily) to renew expiring subscriptions
"""
import os
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PUBSUB_HUB_URL = os.environ.get("PUBSUB_HUB_URL", "https://pubsubhubbub.appspot.com/subscribe")
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL", "http://localhost:8080")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
LEASE_SECONDS = 864000  # 10 days

TARGET_CHANNEL_IDS = [
    id_.strip()
    for id_ in os.environ.get("CHANNEL_IDS", "").split(",")
    if id_.strip()
]


def resubscribe_channel(channel_id: str) -> bool:
    """
    Resubscribe to a specific YouTube channel
    """
    topic_url = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"
    callback_url = f"{WEBHOOK_BASE_URL}/webhook"
    payload = {
        "hub.callback": callback_url,
        "hub.mode": "subscribe",
        "hub.topic": topic_url,
        "hub.verify": "async",
        "hub.secret": WEBHOOK_SECRET,
        "hub.lease_seconds": LEASE_SECONDS,
    }
    
    log.info(f"Resubscribing to channel: {channel_id}")
    
    try:
        resp = requests.post(PUBSUB_HUB_URL, data=payload, timeout=30)
        if resp.status_code in (202, 204):
            log.info(f"✓ Successfully resubscribed to channel {channel_id}")
            return True
        else:
            log.error(f"✗ Failed to resubscribe to {channel_id}: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        log.error(f"✗ Error resubscribing to {channel_id}: {e}")
        return False


def main():
    """
    Main function to resubscribe to all configured channels
    """
    log.info(f"Starting resubscription process for {len(TARGET_CHANNEL_IDS)} channels...")
    
    if not TARGET_CHANNEL_IDS:
        log.error("No CHANNEL_IDS found in environment. Please set CHANNEL_IDS in .env")
        return
    
    successful_resubs = 0
    for channel_id in TARGET_CHANNEL_IDS:
        if resubscribe_channel(channel_id):
            successful_resubs += 1
    
    log.info(f"Resubscription process completed: {successful_resubs}/{len(TARGET_CHANNEL_IDS)} successful")


if __name__ == "__main__":
    main()