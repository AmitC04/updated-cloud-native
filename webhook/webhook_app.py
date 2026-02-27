"""
webhook/webhook_app.py
FastAPI webhook receiver for PubSubHubbub notifications.
Handles YouTube video publish notifications in real-time.
"""
import os
import hashlib
import hmac
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
import uvicorn
import asyncio

from db import build_video_doc, upsert_video

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube Video Ingestion Webhook")

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Handle webhook verification challenge from PubSubHubbub hub.
    Must return plain text response with challenge.
    """
    challenge = request.query_params.get("hub.challenge")
    mode = request.query_params.get("hub.mode")
    topic = request.query_params.get("hub.topic")
    lease_seconds = request.query_params.get("hub.lease_seconds")
    
    logger.info(f"PubSubHubbub Verification Request - Mode: {mode}, Topic: {topic}, Lease: {lease_seconds}s")
    
    if not challenge:
        logger.error("Missing challenge parameter in verification request")
        raise HTTPException(status_code=400, detail="Missing challenge parameter")
    
    # Return plain text challenge as required by PubSubHubbub spec
    return PlainTextResponse(challenge)


@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Process incoming YouTube video notifications from PubSubHubbub.
    Verifies HMAC signature if secret is configured.
    """
    logger.info("Received webhook POST request")
    
    # Get request body for signature verification
    body = await request.body()
    
    # Verify signature if secret is configured
    expected_signature = request.headers.get("X-Hub-Signature")
    if expected_signature:
        secret = os.environ.get("WEBHOOK_SECRET", "").encode()
        if secret:
            # PubSubHubbub uses sha1 signature
            signature = hmac.new(
                secret, body, hashlib.sha1
            ).hexdigest()
            expected_hash = expected_signature.replace("sha1=", "").strip()
            
            if not hmac.compare_digest(signature, expected_hash):
                logger.error("Invalid signature on webhook request")
                raise HTTPException(status_code=403, detail="Invalid signature")
            logger.info("Webhook signature verified successfully")
    
    content_type = request.headers.get("Content-Type", "")
    
    # Handle Atom feed (XML) format
    if "application/atom+xml" in content_type or "application/xml" in content_type:
        try:
            root = ET.fromstring(body.decode('utf-8'))
            logger.debug(f"XML root tag: {root.tag}")
            
            # Extract video information from Atom feed
            # Namespace for Atom
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'yt': 'http://www.youtube.com/xml/schemas/2015/internalstats.xsd'
            }
            
            entries = root.findall("atom:entry", ns)
            logger.info(f"Found {len(entries)} entries in webhook")
            
            for entry in entries:
                video_data = {}
                
                # Extract video ID from link
                links = entry.findall("atom:link", ns)
                for link in links:
                    href = link.get("href", "")
                    if "youtube.com/watch" in href:
                        # Extract video ID from URL
                        if "v=" in href:
                            video_id = href.split("v=")[1].split("&")[0]
                            video_data["video_id"] = video_id
                            video_data["url"] = href
                            logger.info(f"Extracted video ID: {video_id}")
                        break
                
                # Extract other fields from Atom feed
                title_elem = entry.find("atom:title", ns)
                if title_elem is not None and title_elem.text:
                    video_data["title"] = title_elem.text
                
                # Extract author/channel information
                author_elem = entry.find("atom:author/atom:name", ns)
                if author_elem is not None and author_elem.text:
                    video_data["channel"] = author_elem.text
                
                author_uri_elem = entry.find("atom:author/atom:uri", ns)
                if author_uri_elem is not None and author_uri_elem.text:
                    video_data["channel_url"] = author_uri_elem.text
                
                # Extract publish date
                published_elem = entry.find("atom:published", ns)
                if published_elem is not None and published_elem.text:
                    video_data["upload_date"] = published_elem.text
                
                # Updated date as fallback
                updated_elem = entry.find("atom:updated", ns)
                if updated_elem is not None and updated_elem.text and "upload_date" not in video_data:
                    video_data["upload_date"] = updated_elem.text
                
                # Add source indicator
                video_data["_source"] = "pubsubhubbub"
                
                # Validate we have minimum required data
                if "video_id" in video_data and "title" in video_data:
                    # Process in background to return quickly (as per PubSubHubbub spec)
                    background_tasks.add_task(process_video_notification, video_data)
                    logger.info(f"Queued video for processing: {video_data.get('title', video_data.get('video_id'))}")
                else:
                    logger.warning(f"Incomplete video data: {video_data}")
            
            logger.info(f"Successfully processed webhook with {len(entries)} entries")
            return {"status": "received", "count": len(entries)}
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid XML: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error processing notification: {str(e)}")
    else:
        logger.error(f"Unsupported content type: {content_type}")
        raise HTTPException(status_code=400, detail="Unsupported content type")


def process_video_notification(video_data: dict):
    """
    Process the video notification in the background.
    Builds database document and upserts video metadata.
    """
    try:
        logger.info(f"Processing video: {video_data.get('video_id', 'unknown')}")
        
        # Build document from raw data
        doc = build_video_doc(video_data)
        
        # Upsert into database
        is_new = upsert_video(doc)
        
        action = "Inserted" if is_new else "Updated"
        logger.info(f"{action} video: {doc['video_id']} - {doc['title']}")
        
    except Exception as e:
        logger.error(f"Error processing video notification for {video_data.get('video_id')}: {str(e)}", exc_info=True)


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "service": "webhook"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "YouTube Video Webhook", "status": "ready", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)