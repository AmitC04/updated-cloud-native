"""
webhook/subscribe.py
Manages PubSubHubbub subscriptions to YouTube channel feeds.
Handles subscription creation, renewal, and health checks.
"""
import os
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PubSubHubbub Hub endpoint
PUBSUB_HUB_URL = os.environ.get(
    "PUBSUB_HUB_URL",
    "https://pubsubhubbub.appspot.com/subscribe"
)

# Webhook base URL (must be accessible from internet)
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL", "http://localhost:8080")
WEBHOOK_PATH = "/webhook"

# Target YouTube channels - Channel IDs
CHANNEL_IDS = [
    "UCIALMKvObZNtJ6AmdCLP7Lg",  # Bloomberg Markets
    "UCtFQDgA8J8_iiwc5-KoAQlg",  # ANI News India
]

# Channel ID to friendly name mapping
CHANNEL_NAMES = {
    "UCIALMKvObZNtJ6AmdCLP7Lg": "Bloomberg Markets",
    "UCtFQDgA8J8_iiwc5-KoAQlg": "ANI News India",
}


def get_channel_feed_url(channel_id: str) -> str:
    """
    Construct the YouTube channel feed URL for PubSubHubbub.
    YouTube feeds follow: https://www.youtube.com/xml/feeds/videos.xml?channel_id=CHANNEL_ID
    """
    return f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"


def subscribe_to_channel(channel_id: str) -> Tuple[bool, str]:
    """
    Subscribe to a YouTube channel using PubSubHubbub.
    
    Args:
        channel_id: YouTube channel ID
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    channel_name = CHANNEL_NAMES.get(channel_id, channel_id)
    logger.info(f"Subscribing to channel: {channel_name} ({channel_id})")
    
    # Construct the topic (channel feed URL)
    topic = get_channel_feed_url(channel_id)
    
    # Construct the callback URL
    callback = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"
    
    # Prepare subscription request
    data = {
        "hub.callback": callback,
        "hub.mode": "subscribe",
        "hub.topic": topic,
        "hub.lease_seconds": "432000",  # 5 days
        "hub.secret": os.environ.get("WEBHOOK_SECRET", ""),
    }
    
    try:
        logger.debug(f"Sending subscription request to: {PUBSUB_HUB_URL}")
        logger.debug(f"Topic: {topic}")
        logger.debug(f"Callback: {callback}")
        
        response = requests.post(
            PUBSUB_HUB_URL,
            data=data,
            timeout=30
        )
        
        logger.info(f"Subscription response status: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response body: {response.text}")
        
        if response.status_code in [204, 200]:
            logger.info(f"✓ Successfully subscribed to {channel_name}")
            return True, f"Successfully subscribed to {channel_name}"
        elif response.status_code == 202:
            logger.info(f"✓ Subscription request accepted for {channel_name} (async processing)")
            return True, f"Subscription request accepted for {channel_name}"
        else:
            error_msg = f"Failed to subscribe to {channel_name}: HTTP {response.status_code}"
            logger.error(error_msg)
            logger.error(f"Response: {response.text}")
            return False, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = f"Timeout while connecting to PubSubHubbub hub"
        logger.error(error_msg)
        return False, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to subscribe to {channel_name}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error subscribing to {channel_name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def unsubscribe_from_channel(channel_id: str) -> Tuple[bool, str]:
    """
    Unsubscribe from a YouTube channel using PubSubHubbub.
    
    Args:
        channel_id: YouTube channel ID
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    channel_name = CHANNEL_NAMES.get(channel_id, channel_id)
    logger.info(f"Unsubscribing from channel: {channel_name} ({channel_id})")
    
    topic = get_channel_feed_url(channel_id)
    callback = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"
    
    data = {
        "hub.callback": callback,
        "hub.mode": "unsubscribe",
        "hub.topic": topic,
    }
    
    try:
        response = requests.post(
            PUBSUB_HUB_URL,
            data=data,
            timeout=30
        )
        
        if response.status_code in [204, 200, 202]:
            logger.info(f"✓ Successfully unsubscribed from {channel_name}")
            return True, f"Unsubscribed from {channel_name}"
        else:
            error_msg = f"Failed to unsubscribe from {channel_name}: HTTP {response.status_code}"
            logger.error(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Failed to unsubscribe from {channel_name}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def subscribe_all_channels() -> Tuple[int, int]:
    """
    Subscribe to all target channels.
    
    Returns:
        Tuple of (successful: int, failed: int)
    """
    logger.info("=" * 60)
    logger.info("SUBSCRIBING TO ALL YOUTUBE CHANNELS")
    logger.info("=" * 60)
    
    successful = 0
    failed = 0
    
    for channel_id in CHANNEL_IDS:
        success, message = subscribe_to_channel(channel_id)
        logger.info(message)
        
        if success:
            successful += 1
        else:
            failed += 1
    
    logger.info("=" * 60)
    logger.info(f"Subscription Summary: {successful} successful, {failed} failed")
    logger.info("=" * 60)
    
    return successful, failed


def unsubscribe_all_channels() -> Tuple[int, int]:
    """
    Unsubscribe from all target channels.
    
    Returns:
        Tuple of (successful: int, failed: int)
    """
    logger.info("=" * 60)
    logger.info("UNSUBSCRIBING FROM ALL YOUTUBE CHANNELS")
    logger.info("=" * 60)
    
    successful = 0
    failed = 0
    
    for channel_id in CHANNEL_IDS:
        success, message = unsubscribe_from_channel(channel_id)
        logger.info(message)
        
        if success:
            successful += 1
        else:
            failed += 1
    
    logger.info("=" * 60)
    logger.info(f"Unsubscription Summary: {successful} successful, {failed} failed")
    logger.info("=" * 60)
    
    return successful, failed


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "unsubscribe":
        unsubscribe_all_channels()
    else:
        subscribe_all_channels()
