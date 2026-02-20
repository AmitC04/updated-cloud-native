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
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import uvicorn
import asyncio

from db import build_video_doc, upsert_video

app = FastAPI(title="YouTube Video Ingestion Webhook")

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Handle webhook verification challenge from PubSubHubbub hub
    """
    challenge = request.query_params.get("hub.challenge")
    if challenge:
        return {"challenge": challenge}
    raise HTTPException(status_code=400, detail="Missing challenge parameter")


@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Process incoming YouTube video notifications from PubSubHubbub
    """
    # Verify signature if secret is configured
    expected_signature = request.headers.get("X-Hub-Signature")
    if expected_signature:
        body = await request.body()
        secret = os.environ.get("WEBHOOK_SECRET", "")  # Load from environment
        if secret:
            signature = hmac.new(
                secret.encode(), body, hashlib.sha1
            ).hexdigest()
            expected_hash = expected_signature.replace("sha1=", "")
            
            if not hmac.compare_digest(signature, expected_hash):
                raise HTTPException(status_code=403, detail="Invalid signature")
    
    content_type = request.headers.get("Content-Type", "")
    if "application/atom+xml" in content_type or "application/xml" in content_type:
        body = await request.body()
        try:
            root = ET.fromstring(body.decode('utf-8'))
            
            # Extract video information from Atom feed
            entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
            
            for entry in entries:
                video_data = {}
                
                # Extract video ID from link
                links = entry.findall(".//{http://www.w3.org/2005/Atom}link")
                for link in links:
                    href = link.get("href", "")
                    if "youtube.com/watch" in href:
                        video_id = href.split("v=")[1].split("&")[0]
                        video_data["video_id"] = video_id
                        video_data["url"] = href
                        break
                
                # Extract other fields
                title_elem = entry.find(".//{http://www.w3.org/2005/Atom}title")
                if title_elem is not None:
                    video_data["title"] = title_elem.text or ""
                
                author_elem = entry.find(".//{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name")
                if author_elem is not None:
                    video_data["channel"] = author_elem.text or ""
                
                author_uri_elem = entry.find(".//{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}uri")
                if author_uri_elem is not None:
                    video_data["channel_url"] = author_uri_elem.text or ""
                
                published_elem = entry.find(".//{http://www.w3.org/2005/Atom}published")
                if published_elem is not None:
                    video_data["upload_date"] = published_elem.text or ""
                
                updated_elem = entry.find(".//{http://www.w3.org/2005/Atom}updated")
                if updated_elem is not None and "upload_date" not in video_data:
                    video_data["upload_date"] = updated_elem.text or ""
                
                # Add source indicator
                video_data["_source"] = "pubsubhubbub"
                
                # Process in background to return quickly
                background_tasks.add_task(process_video_notification, video_data)
            
            return {"status": "received", "count": len(entries)}
        except ET.ParseError as e:
            raise HTTPException(status_code=400, detail=f"Invalid XML: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing notification: {str(e)}")
    
    raise HTTPException(status_code=400, detail="Unsupported content type")


def process_video_notification(video_data: dict):
    """
    Process the video notification in the background
    """
    try:
        # Build document from raw data
        doc = build_video_doc(video_data)
        
        # Upsert into database
        is_new = upsert_video(doc)
        
        print(f"{'Inserted' if is_new else 'Updated'} video: {doc['video_id']} - {doc['title']}")
        
    except Exception as e:
        print(f"Error processing video notification: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)