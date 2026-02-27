"""
chatbot/agents.py
AI agents using Groq LLM with real-time MongoDB context injection.
"""
import os
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from groq import Groq
from db import get_videos_collection
from query_db import (
    search_videos,
    get_videos_by_channel,
    get_top_videos,
    get_trending_videos,
    get_video_statistics
)
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Groq client
_groq_api_key = os.environ.get("GROQ_API_KEY", "")
if not _groq_api_key:
    logger.warning("GROQ_API_KEY not configured")
_groq_client: Groq = None

def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=_groq_api_key)
    return _groq_client

GROQ_MODEL = "llama-3.3-70b-versatile"


def count_videos_by_channel(channel_name: str) -> str:
    """Count videos for a specific channel"""
    try:
        collection = get_videos_collection()
        count = collection.count_documents({"channel": {"$regex": channel_name, "$options": "i"}})
        logger.info(f"Count for {channel_name}: {count}")
        return f"Found **{count}** videos from {channel_name}."
    except Exception as e:
        logger.error(f"Error counting videos for {channel_name}: {e}")
        return f"Error counting videos: {str(e)}"


def videos_last_24h(channel_name: str = None) -> str:
    """Get videos from last 24 hours"""
    try:
        collection = get_videos_collection()
        
        # Calculate 24h ago
        time_24h_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        query = {"upload_date": {"$gte": time_24h_ago}}
        if channel_name:
            query["channel"] = {"$regex": channel_name, "$options": "i"}
        
        videos = list(collection.find(query).sort("upload_date", -1).limit(10))
        
        if not videos:
            return f"No videos found in the last 24 hours{f' from {channel_name}' if channel_name else ''}."
        
        response = f"**{len(videos)} videos from last 24 hours:**\n\n"
        for i, vid in enumerate(videos, 1):
            response += f"{i}. **{vid['title']}** ({vid['channel']})\n"
            response += f"   Published: {vid['upload_date']}\n"
            response += f"   Views: {vid['view_count']:,} | Likes: {vid['like_count']:,}\n\n"
        
        logger.info(f"Found {len(videos)} videos from last 24h")
        return response
    except Exception as e:
        logger.error(f"Error fetching last 24h videos: {e}")
        return f"Error fetching videos: {str(e)}"


def search_videos_by_topic(query: str, limit: int = 10) -> str:
    """Search for videos by topic/keyword"""
    try:
        videos = search_videos(text_query=query, limit=limit)
        
        if not videos:
            return f"No videos found for '{query}'."
        
        response = f"**{len(videos)} videos about '{query}':**\n\n"
        for i, vid in enumerate(videos, 1):
            response += f"{i}. **{vid['title']}** ({vid['channel']})\n"
            response += f"   {vid['description'][:100]}...\n"
            response += f"   Views: {vid['view_count']:,}\n\n"
        
        logger.info(f"Found {len(videos)} videos for topic: {query}")
        return response
    except Exception as e:
        logger.error(f"Error searching for topic {query}: {e}")
        return f"Error searching videos: {str(e)}"


def videos_about_country(country_name: str, limit: int = 10) -> str:
    """Find videos about a specific country"""
    try:
        videos = search_videos(text_query=country_name, limit=limit)
        
        if not videos:
            return f"No videos found about {country_name}."
        
        response = f"**{len(videos)} videos about {country_name}:**\n\n"
        for i, vid in enumerate(videos, 1):
            response += f"{i}. **{vid['title']}** ({vid['channel']})\n"
            response += f"   Published: {vid['upload_date']}\n"
            response += f"   Views: {vid['view_count']:,}\n\n"
        
        logger.info(f"Found {len(videos)} videos about {country_name}")
        return response
    except Exception as e:
        logger.error(f"Error searching for {country_name}: {e}")
        return f"Error searching videos: {str(e)}"


def get_trending_topics(limit: int = 10) -> str:
    """Get trending topics from video titles"""
    try:
        collection = get_videos_collection()
        
        # Get top videos by view count
        top_videos = list(collection.find({}).sort("view_count", -1).limit(min(limit * 2, 50)))
        
        # Extract common words from titles
        from collections import Counter
        all_words = []
        stop_words = {'the', 'a', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'by'}
        
        for video in top_videos:
            words = video['title'].lower().split()
            for word in words:
                word = word.strip('[]().,!?;:\'"')
                if len(word) > 3 and word not in stop_words:
                    all_words.append(word)
        
        word_counts = Counter(all_words)
        trending = word_counts.most_common(limit)
        
        response = f"**Top {min(len(trending), limit)} Trending Topics:**\n\n"
        for i, (topic, count) in enumerate(trending, 1):
            response += f"{i}. **{topic.title()}** (appears in {count} titles)\n"
        
        logger.info(f"Generated trending topics")
        return response
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        return f"Error getting trends: {str(e)}"


def get_database_stats() -> str:
    """Get overall database statistics"""
    try:
        collection = get_videos_collection()
        
        total_videos = collection.count_documents({})
        channels = collection.distinct("channel")
        
        # Get date range
        newest = collection.find_one(sort=[("upload_date", -1)])
        oldest = collection.find_one(sort=[("upload_date", 1)])
        
        response = f"**Database Statistics:**\n\n"
        response += f"📊 **Total Videos:** {total_videos}\n"
        response += f"🎬 **Channels:** {len(channels)}\n"
        
        if newest:
            response += f"📅 **Newest:** {newest['upload_date']}\n"
        if oldest:
            response += f"📅 **Oldest:** {oldest['upload_date']}\n"
        
        response += f"\n**Channels in Database:**\n"
        for channel in sorted(channels):
            count = collection.count_documents({"channel": channel})
            response += f"• {channel}: {count} videos\n"
        
        logger.info("Retrieved database statistics")
        return response
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return f"Error getting statistics: {str(e)}"


def execute_tool(tool_name: str, tool_input: Dict) -> str:
    """Execute a tool function based on name"""
    logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
    
    if tool_name == "count_videos_by_channel":
        return count_videos_by_channel(tool_input.get("channel_name", ""))
    elif tool_name == "videos_last_24h":
        return videos_last_24h(tool_input.get("channel_name"))
    elif tool_name == "search_videos_by_topic":
        return search_videos_by_topic(
            tool_input.get("query", ""),
            tool_input.get("limit", 10)
        )
    elif tool_name == "videos_about_country":
        return videos_about_country(
            tool_input.get("country_name", ""),
            tool_input.get("limit", 10)
        )
    elif tool_name == "get_trending_topics":
        return get_trending_topics(tool_input.get("limit", 10))
    elif tool_name == "get_database_stats":
        return get_database_stats()
    else:
        return f"Unknown tool: {tool_name}"


DB_UNAVAILABLE = "__DB_UNAVAILABLE__"


def _gather_database_context(user_message: str) -> str:
    """
    Fetch all relevant data from the database based on the user's question.
    Returns a rich context string to be injected into the Groq prompt.
    Returns DB_UNAVAILABLE sentinel if the database cannot be reached.
    """
    user_lower = user_message.lower()
    context_parts = []

    STOP_WORDS = {
        'what', 'when', 'where', 'which', 'show', 'give', 'tell', 'find',
        'about', 'videos', 'video', 'from', 'with', 'that', 'have', 'does',
        'were', 'this', 'they', 'some', 'many', 'much', 'the', 'and', 'for',
        'are', 'how', 'can', 'any', 'all', 'get', 'list', 'please', 'like',
        'last', 'more', 'now', 'just', 'into', 'over', 'such', 'than',
    }

    try:
        collection = get_videos_collection()

        # ── Always include baseline stats ──────────────────────────────────
        total = collection.count_documents({})
        channels = collection.distinct("channel")
        context_parts.append(
            f"[DB OVERVIEW] Total videos: {total} | Channels: {', '.join(channels)}"
        )

        # ── Channel-specific data ──────────────────────────────────────────
        for channel in channels:
            channel_lower = channel.lower()
            channel_words = [w for w in channel_lower.split() if len(w) > 2]
            if any(w in user_lower for w in channel_words):
                count = collection.count_documents({"channel": channel})
                context_parts.append(f"[CHANNEL] '{channel}': {count} videos total")
                recent_ch = list(
                    collection.find({"channel": channel})
                    .sort("upload_date", -1).limit(10)
                )
                for v in recent_ch:
                    context_parts.append(
                        f"  • {v['title']} | Date: {v.get('upload_date','N/A')} "
                        f"| Views: {v.get('view_count',0):,} | Likes: {v.get('like_count',0):,}"
                    )

        # ── First / oldest video ───────────────────────────────────────────
        if any(w in user_lower for w in ['first', 'oldest', 'earliest', 'beginning', 'start']):
            oldest = collection.find_one(sort=[("upload_date", 1)])
            if oldest:
                context_parts.append(
                    f"[FIRST VIDEO] '{oldest['title']}' by {oldest['channel']} "
                    f"on {oldest.get('upload_date','N/A')} | "
                    f"Views: {oldest.get('view_count',0):,} | Likes: {oldest.get('like_count',0):,}"
                )

        # ── Latest / newest / recent ───────────────────────────────────────
        if any(w in user_lower for w in ['latest', 'newest', 'recent', 'today', 'new', 'last']):
            newest = collection.find_one(sort=[("upload_date", -1)])
            if newest:
                context_parts.append(
                    f"[NEWEST VIDEO] '{newest['title']}' by {newest['channel']} "
                    f"on {newest.get('upload_date','N/A')}"
                )
            time_24h_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            recent_videos = list(
                collection.find({"upload_date": {"$gte": time_24h_ago}})
                .sort("upload_date", -1).limit(10)
            )
            context_parts.append(f"[LAST 24H] {len(recent_videos)} videos uploaded")
            for v in recent_videos[:5]:
                context_parts.append(
                    f"  • {v['title']} | {v['channel']} | {v.get('upload_date','N/A')}"
                )

        # ── Top / popular / trending ───────────────────────────────────────
        if any(w in user_lower for w in ['top', 'popular', 'most viewed', 'best', 'trending', 'highest']):
            top_videos = list(collection.find({}).sort("view_count", -1).limit(10))
            context_parts.append("[TOP VIDEOS BY VIEWS]")
            for v in top_videos:
                context_parts.append(
                    f"  • {v['title']} | {v['channel']} | "
                    f"Views: {v.get('view_count',0):,} | Likes: {v.get('like_count',0):,}"
                )

        # ── Statistics / counts ────────────────────────────────────────────
        if any(w in user_lower for w in ['stat', 'total', 'count', 'how many', 'overview']):
            try:
                stats = get_video_statistics()
                db_stats = stats.get('database', {})
                overall = stats.get('overall', {})
                context_parts.append(
                    f"[STATS] Videos: {db_stats.get('total_videos','N/A')} | "
                    f"Channels: {db_stats.get('total_channels','N/A')} | "
                    f"Total Views: {overall.get('total_views',0):,} | "
                    f"Total Likes: {overall.get('total_likes',0):,}"
                )
            except Exception as se:
                logger.warning(f"Stats fetch failed: {se}")

        # ── Generic keyword search (fallback for everything else) ──────────
        meaningful_words = [
            w.strip('.,!?;:\'"()[]') for w in user_lower.split()
            if len(w) > 3 and w not in STOP_WORDS
        ]
        if meaningful_words:
            search_query = " ".join(meaningful_words[:6])
            try:
                results = search_videos(text_query=search_query, limit=10)
                if results:
                    context_parts.append(
                        f"[SEARCH '{search_query}'] {len(results)} results:"
                    )
                    for v in results[:8]:
                        context_parts.append(
                            f"  • {v['title']} | {v['channel']} | "
                            f"Date: {v.get('upload_date','N/A')} | "
                            f"Views: {v.get('view_count',0):,}"
                        )
            except Exception as se:
                logger.warning(f"Search failed for '{search_query}': {se}")

    except Exception as e:
        logger.error(f"Error gathering database context: {e}", exc_info=True)
        # Return sentinel — do NOT pass the error text to the LLM
        return DB_UNAVAILABLE

    return "\n".join(context_parts)


def get_chat_response(user_message: str, conversation_history: List[Dict] = None) -> str:
    """
    Get a Groq-powered response grounded in real database data.
    Database context is fetched FIRST and injected into the system prompt so
    the LLM can answer ANY question with real facts from MongoDB.
    """
    try:
        if conversation_history is None:
            conversation_history = []

        logger.info(f"Processing: {user_message[:100]}...")

        # 1. Fetch real data from MongoDB relevant to this question
        db_context = _gather_database_context(user_message)

        # 2. If DB is unreachable, return a clear message — don't confuse Groq
        if db_context == DB_UNAVAILABLE:
            # Try to find public IP to make the fix instructions specific
            public_ip = "your current IP"
            try:
                import urllib.request as _ur
                public_ip = _ur.urlopen("https://api.ipify.org", timeout=4).read().decode()
            except Exception:
                pass
            return (
                "⚠️ **Database Unavailable**\n\n"
                "Cannot connect to MongoDB Atlas. All ports (27017 & 443) to the cluster "
                "are being blocked.\n\n"
                "**Your current public IP:** `" + public_ip + "`\n\n"
                "**Fix in 3 steps:**\n"
                "1. Open [MongoDB Atlas](https://cloud.mongodb.com) → **Security** → **Network Access**\n"
                "2. Click **Add IP Address** → enter `" + public_ip + "` → **Confirm**\n"
                "3. Wait ~30 seconds, then click **🔄 Refresh** in the sidebar\n\n"
                "_After whitelisting, all questions will be answered from live database data._"
            )

        logger.info(f"DB context built ({db_context.count(chr(10))} lines)")

        # 2. System prompt with injected live data
        system_prompt = f"""You are an intelligent AI assistant for a YouTube video analytics dashboard.
You have been given LIVE DATA retrieved directly from the MongoDB database right now.
Use this data to answer the user's question accurately and completely.
Never say you lack access to data — all relevant data is provided below.
Format ALL responses using markdown: use **bold**, bullet points, numbered lists, and headers.
Be concise but thorough. Highlight key numbers and facts.

=== LIVE DATABASE DATA ===
{db_context}
=== END OF DATA ===

Answer based on the data above. If something is not in the data, say so honestly and suggest related queries."""

        # 3. Build conversation history in OpenAI format
        messages: List[Dict] = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-8:]:   # keep last 8 turns for context
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        # 4. Call Groq
        client = _get_groq_client()
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        response_text = completion.choices[0].message.content
        logger.info(f"Response length: {len(response_text)}")
        return response_text

    except Exception as e:
        logger.error(f"Error in get_chat_response: {e}", exc_info=True)
        return _fallback_response(user_message)


def _fallback_response(user_message: str) -> str:
    """
    Fallback response when AI fails - use direct database queries
    """
    user_lower = user_message.lower()
    
    try:
        # Search query
        if any(word in user_lower for word in ["search", "find", "about", "video"]):
            results = search_videos(text_query=user_message, limit=5)
            if results:
                response = f"Found {len(results)} videos:\n\n"
                for i, video in enumerate(results, 1):
                    response += f"{i}. **{video.get('title', 'N/A')}**\n"
                    response += f"   • Views: {video.get('view_count', 0):,}\n"
                    response += f"   • Likes: {video.get('like_count', 0):,}\n"
                return response
        
        # Channel query
        if any(word in user_lower for word in ["bloomberg", "ani", "channel"]):
            for channel_name in ["Bloomberg", "ANI"]:
                if channel_name.lower() in user_lower:
                    collection = get_videos_collection()
                    count = collection.count_documents({"channel": {"$regex": channel_name, "$options": "i"}})
                    return f"**{channel_name}** has **{count}** videos in the database."
        
        # Stats query
        if any(word in user_lower for word in ["statistics", "stats", "total", "how many"]):
            stats = get_video_statistics()
            response = "📊 **Database Statistics:**\n\n"
            response += f"• Total Videos: {stats['database']['total_videos']}\n"
            response += f"• Total Channels: {stats['database']['total_channels']}\n"
            if stats['overall']:
                response += f"• Total Views: {stats['overall'].get('total_views', 0):,}\n"
            return response
        
    except Exception as e:
        logger.warning(f"Fallback response error: {str(e)}")
    
    return "I can help you find videos, search for topics, or get statistics. What would you like to know?"


def get_demo_response(user_message: str) -> str:
    """
    Get demo response when API key is not available
    Shows realistic example responses based on the query
    """
    user_lower = user_message.lower()
    
    # Demo responses based on keywords
    if any(word in user_lower for word in ["bloomberg", "markets", "how many", "count"]):
        return """
📊 **Bloomberg Markets Videos: 245**

From the database:
- **Total Videos**: 245 videos from Bloomberg Markets channel
- **Date Range**: Jan 2024 - Present
- **Average Views**: ~15,000 per video
- **Most Popular**: "Federal Reserve Decision Analysis" (89K views)
- **Last Updated**: Today at 2:45 PM

💡 *Try asking: "Latest Bloomberg videos" or "Bloomberg economy videos"*
"""
    
    elif any(word in user_lower for word in ["ani", "india", "indian", "news"]):
        return """
🇮🇳 **ANI News India Statistics**

From the database:
- **Total Videos**: 412 videos from ANI News India
- **Date Range**: Feb 2024 - Present
- **Average Views**: ~8,500 per video
- **Top Category**: Breaking News
- **Engagement**: High likes ratio (3.2%)
- **Subscribers Based**: 2.1M+ subscribers

💡 *Try asking: "Latest ANI news videos" or "ANI videos about politics"*
"""
    
    elif any(word in user_lower for word in ["economy", "economic", "financial", "market", "stock"]):
        return """
📈 **Economy & Financial Markets Videos**

**Search Results: 156 videos found**

Top 3 with highest engagement:
1. 📹 "Federal Reserve Raises Interest Rates" - 125K views, 3.2K likes
2. 📹 "Stock Market Analysis 2024" - 98K views, 2.8K likes
3. 📹 "Global Economic Outlook" - 76K views, 2.1K likes

🎯 **Insights:**
- Keywords: inflation, GDP, crypto, bonds, stocks
- Most Recent: Today's market update
- Trending: Banking sector news

💡 *Try asking: "Most viewed economy videos" or "Recent financial news"*
"""
    
    elif any(word in user_lower for word in ["last 24", "recent", "today", "latest"]):
        return """
⏰ **Videos from Last 24 Hours**

**Total: 23 new videos**

Latest uploads:
1. 🎥 **Bloomberg Markets** (2 hours ago) - "Tech Stock Rally Analysis"
2. 🎥 **ANI News India** (4 hours ago) - "Government Economic Reforms"
3. 🎥 **Bloomberg Markets** (6 hours ago) - "Currency Market Trends"
4. 🎥 **ANI News India** (8 hours ago) - "Infrastructure Development"
5. 🎥 **Bloomberg Markets** (12 hours ago) - "Global Trade Updates"

📊 **Statistics:**
- Bloomberg: 12 videos | ANI: 11 videos
- Total Views: 234K | Engagement: Very High

💡 *Try asking: "Last 24h Bloomberg videos" or "Today's top videos"*
"""
    
    elif any(word in user_lower for word in ["top", "trending", "popular", "most viewed", "best"]):
        return """
🏆 **Top Trending Videos**

**Most Viewed (All Time):**
1. 🥇 "Federal Reserve Complete Analysis" - **245K views**
2. 🥈 "Stock Market Crash Explained" - **189K views**
3. 🥉 "Global Economic Crisis" - **176K views**

**Most Liked:**
1. ❤️ "Economic Recovery Strategies" - **4.2K likes**
2. ❤️ "Investment Tips for 2024" - **3.8K likes**
3. ❤️ "Market Forecasting 101" - **3.1K likes**

**Most Discussed:**
- Comments: 8,234 total across all trending videos
- Engagement Rate: 4.2% (excellent!)

💡 *Try asking: "Top videos this week" or "Most liked videos"*
"""
    
    elif any(word in user_lower for word in ["statistics", "stats", "database", "total"]):
        return """
📊 **Database Statistics**

**Overall Metrics:**
- 📹 Total Videos: 657 videos
- 📺 Channels: 2 major channels
  - Bloomberg Markets: 245 videos
  - ANI News India: 412 videos
- 👁️ Total Views: 12.3M views
- ❤️ Total Likes: 285K likes
- 💬 Total Comments: 45K comments

**Engagement Metrics:**
- Average Views/Video: 18.7K
- Average Likes/Video: 433
- Average Comments/Video: 68

**Time Range:**
- Earliest: Jan 15, 2024
- Latest: Today
- Duration: 37 days

**Performance:**
- Views/Day: 332K (avg)
- Engagement Rate: 3.8%

💡 *Try asking: "Latest Bloomberg videos" or "Videos from specific date"*
"""
    
    else:
        # Generic response for unknown queries
        return f"""
🤔 **Your Question: "{user_message}"**

I can help you with:
- 📺 Find videos by **channel** (Bloomberg or ANI News)
- 🔍 **Search** for videos by topic (economics, markets, news)
- 📊 Get **statistics** and analytics
- ⏰ Filter by **time period** (last 24h, this week)
- 🏆 Find **top videos** by views or likes
- 📈 Get **trends** and insights

**Example Queries:**
- "How many Bloomberg videos?"
- "Videos about economy in last 24 hours"
- "Show me most popular videos"
- "Latest ANI news videos"
- "Database statistics"

💡 *Set GEMINI_API_KEY to enable AI-powered natural language responses!*

---
**Note:** This is demo mode. Enable with your Gemini API key for real AI responses.
"""