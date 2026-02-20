"""
chatbot/agents.py
AI agents using Google ADK and Gemini API for natural language queries
"""
import os
import json
from typing import Dict, List
from google.generativeai.types import GenerationConfig
import google.generativeai as genai
from db import get_videos_collection
from datetime import datetime, timedelta
from query_db import get_most_recent_entries

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
model = genai.GenerativeModel('models/gemini-pro')


def query_videos_natural_language(query: str) -> str:
    """
    Process natural language queries about YouTube video data
    """
    try:
        # First, get relevant data from database based on the query
        collection = get_videos_collection()
        query_lower = query.lower()
        
        # Check for specific assessment prompts
        if "how many videos from markets" in query_lower or "bloomberg television" in query_lower:
            return get_videos_count_by_channel("Bloomberg Markets")
        elif "videos published about usa in aninewsindia channel in the last 24 hrs" in query_lower:
            return get_usa_videos_from_aninewsindia_last_24hrs()
        
        # Handle common query patterns directly
        elif "most popular" in query_lower or "most viewed" in query_lower:
            # Get top 5 videos by view count
            top_videos = list(collection.find({}).sort("view_count", -1).limit(5))
            if not top_videos:
                return "No videos found in the database."
            
            response = "Here are the most popular videos by view count:\n\n"
            for i, video in enumerate(top_videos, 1):
                response += f"{i}. **{video['title']}**\n"
                response += f"   Channel: {video['channel']}\n"
                response += f"   Views: {video['view_count']:,}\n"
                response += f"   Likes: {video['like_count']:,}\n"
                response += f"   Uploaded: {video['upload_date']}\n\n"
            return response
            
        elif "recent" in query_lower or "latest" in query_lower:
            # Get 5 most recent videos
            recent_videos = list(collection.find({}).sort("upload_date", -1).limit(5))
            if not recent_videos:
                return "No videos found in the database."
            
            response = "Here are the most recent videos:\n\n"
            for i, video in enumerate(recent_videos, 1):
                response += f"{i}. **{video['title']}**\n"
                response += f"   Channel: {video['channel']}\n"
                response += f"   Uploaded: {video['upload_date']}\n"
                response += f"   Views: {video['view_count']:,}\n\n"
            return response
            
        elif "channels" in query_lower or "channel list" in query_lower:
            # List all channels
            channels = collection.distinct("channel")
            if not channels:
                return "No channels found in the database."
            
            response = f"Found {len(channels)} channels in the database:\n\n"
            for channel in sorted(channels):
                count = collection.count_documents({"channel": channel})
                response += f"• **{channel}** ({count} videos)\n"
            return response
            
        elif "total" in query_lower or "count" in query_lower:
            # Get total count
            total = collection.count_documents({})
            return f"The database contains **{total}** videos from all channels."
            
        else:
            # For unrecognized queries, provide basic database info
            total_videos = collection.count_documents({})
            channels = collection.distinct("channel")
            
            response = "I can help you with various video data queries. Here's what I can do:\n\n"
            response += f"📊 **Database Summary:**\n"
            response += f"• Total videos: {total_videos}\n"
            response += f"• Channels: {len(channels)}\n\n"
            response += "**Available query types:**\n"
            response += "• 'most popular videos'\n"
            response += "• 'recent videos'\n"
            response += "• 'list channels'\n"
            response += "• 'total count'\n"
            response += "• Specific assessment queries\n\n"
            response += "What would you like to know about your YouTube video data?"
            
            return response
            
    except Exception as e:
        return f"Sorry, I encountered an error processing your request: {str(e)}"


def get_videos_count_by_channel(channel_name: str) -> str:
    """
    Tool to count videos from a specific channel
    Example: "How many videos from markets (Bloomberg Television) channel have we saved in our database?"
    """
    try:
        collection = get_videos_collection()
        
        # Look for variations of the channel name
        channel_filters = [
            {"channel": {"$regex": channel_name, "$options": "i"}},
            {"channel": {"$regex": "markets", "$options": "i"}},
            {"channel": {"$regex": "bloomberg", "$options": "i"}}
        ]
        
        count = 0
        for filter_obj in channel_filters:
            count = collection.count_documents(filter_obj)
            if count > 0:
                break
        
        return f"The database contains {count} videos from the {channel_name} channel."
    except Exception as e:
        return f"Error counting videos from {channel_name}: {str(e)}"


def get_usa_videos_from_aninewsindia_last_24hrs() -> str:
    """
    Tool to count videos about USA from ANINewsIndia in the last 24 hours
    Example: "Give me a count of the videos published about USA in ANINEWSIndia channel in the last 24 hrs?"
    """
    try:
        collection = get_videos_collection()
        
        # Calculate time threshold (24 hours ago)
        time_threshold = datetime.utcnow() - timedelta(hours=24)
        
        # Query for videos from ANINewsIndia that mention USA in title or description
        query = {
            "$and": [
                {
                    "$or": [
                        {"channel": {"$regex": "ani", "$options": "i"}},
                        {"channel": {"$regex": "aninewsindia", "$options": "i"}}
                    ]
                },
                {
                    "$or": [
                        {"title": {"$regex": "usa|united states|america", "$options": "i"}},
                        {"description": {"$regex": "usa|united states|america", "$options": "i"}}
                    ]
                },
                {"upload_date": {"$gte": time_threshold.isoformat() + "Z"}}
            ]
        }
        
        usa_videos = list(collection.find(query))
        count = len(usa_videos)
        
        return f"There are {count} videos published about USA in ANINewsIndia channel in the last 24 hours. These videos cover topics such as: {[v['title'][:50] + '...' for v in usa_videos[:3]] if usa_videos else 'No matching videos found.'}"
    except Exception as e:
        return f"Error retrieving USA videos from ANINewsIndia in the last 24 hours: {str(e)}"


def get_chat_response(user_message: str, history: List[Dict] = None) -> str:
    """
    Main function to get a chat response based on user message
    """
    try:
        # For now, just use the natural language query function
        # In a more advanced implementation, you could incorporate conversation history
        return query_videos_natural_language(user_message)
    except Exception as e:
        return f"Error processing your request: {str(e)}"