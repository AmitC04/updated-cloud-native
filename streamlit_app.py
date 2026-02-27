"""
📺 YouTube Intelligence Hub
Production-ready Streamlit chatbot powered by Google Generative AI (Gemini)
with MongoDB backend for real-time YouTube video data analysis
"""

import streamlit as st
import os
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════════════════════
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)
sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="YouTube Intelligence Hub",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS & THEMING
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');

html, body, [class*="css"] {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    color: #f1f5f9;
}

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

h1, h2, h3 {
    color: #f0f9ff !important;
    font-weight: 700 !important;
}

.stButton > button {
    background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
}

#MainMenu { visibility: hidden; }
header { visibility: hidden; }
footer { visibility: hidden; }

.block-container {
    padding-top: 2rem !important;
}

.ViewerBadge_container__1QSob {
    visibility: hidden;
}

.stMarkdown {
    line-height: 1.6;
}

.stSpinner > div > div > span {
    color: #3b82f6 !important;
}

.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
}

[data-testid="dataframe"] {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
}

hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, rgba(148, 163, 184, 0), rgba(148, 163, 184, 0.2), rgba(148, 163, 184, 0));
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS & DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from google import genai
    from streamlit_option_menu import option_menu
    from db import get_videos_collection
    from query_db import (
        search_videos,
        get_videos_by_channel,
        get_top_videos,
        get_recent_videos,
        count_videos_by_channel,
        get_videos_by_date_range,
        get_channel_stats,
        get_videos_last_24h,
    )
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError as e:
    st.error(f"❌ Missing dependency: {e}")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# GOOGLE API SETUP
# ═══════════════════════════════════════════════════════════════════════════════
_gemini_client = None
if st.session_state.api_key:
    try:
        _gemini_client = genai.Client(api_key=st.session_state.api_key)
    except Exception:
        _gemini_client = None

# ═══════════════════════════════════════════════════════════════════════════════
# DB-FIRST QUERY ENGINE  (always hits DB, then optionally polishes with Gemini)
# ═══════════════════════════════════════════════════════════════════════════════

def _fmt_videos(videos, limit=10):
    """Format video list into readable markdown."""
    lines = []
    for i, v in enumerate(videos[:limit], 1):
        title   = v.get("title", "N/A")
        channel = v.get("channel") or v.get("channel_id") or "N/A"
        views   = v.get("view_count", 0)
        date    = (v.get("upload_date") or "N/A")[:10]
        vid_id  = v.get("video_id", "")
        url     = v.get("url") or f"https://www.youtube.com/watch?v={vid_id}"
        lines.append(
            f"{i}. **{title}**  \n"
            f"   📺 {channel} | 👁️ {views:,} views | 📅 {date}  \n"
            f"   🔗 [Watch]({url})"
        )
    return "\n\n".join(lines)


def _query_and_answer(user_message: str) -> str:
    """
    Step 1 – query the real DB based on intent detection.
    Step 2 – optionally ask Gemini to format/enrich the answer.
    Step 3 – fallback: return plain formatted answer if Gemini fails.
    """
    msg = user_message.lower()
    context_parts = []

    # ── count / how many ──────────────────────────────────────────────────
    if any(w in msg for w in ["how many", "count", "total", "number of"]):
        if "bloomberg" in msg:
            n = count_videos_by_channel("Bloomberg")
            context_parts.append(f"The YouTube Data API is currently tracking **{n} videos** from the Bloomberg Markets channel via our real-time PubSubHubbub webhook pipeline.")
        elif "ani" in msg or "news india" in msg:
            n = count_videos_by_channel("ANI News India")
            context_parts.append(f"The YouTube Data API is currently tracking **{n} videos** from the ANI News India channel via our real-time PubSubHubbub webhook pipeline.")
        else:
            stats = get_channel_stats()
            total = sum(stats.values())
            context_parts.append(f"Our YouTube pipeline has ingested **{total} videos** in real-time across all monitored channels:")
            for ch, cnt in stats.items():
                context_parts.append(f"• {ch}: {cnt} videos")

    # ── last 24 h / today / recent / latest ───────────────────────────────
    if any(w in msg for w in ["24h", "24 h", "last 24", "today", "recent", "latest"]):
        ch = None
        if "bloomberg" in msg:
            ch = "Bloomberg"
        elif "ani" in msg or "news india" in msg:
            ch = "ANI News India"
        vids = get_videos_last_24h(channel=ch)
        if vids:
            context_parts.append(
                f"✅ **{len(vids)} videos** have been ingested via webhook in the last 24 hours ({ch or 'all channels'}):\n\n"
                + _fmt_videos(vids, 5)
            )
        else:
            vids = get_recent_videos(limit=5, channel=ch)
            context_parts.append(
                f"Latest videos streamed in from YouTube ({ch or 'all channels'}):\n\n" + _fmt_videos(vids, 5)
            )

    # ── popular / top / trending ──────────────────────────────────────────
    if any(w in msg for w in ["popular", "top", "most viewed", "trending", "viral", "best"]):
        vids = get_top_videos(limit=10)
        context_parts.append("**🔥 Top 10 most viewed videos fetched from YouTube:**\n\n" + _fmt_videos(vids, 10))

    # ── keyword search using quoted terms or common prepositions ──────────
    keywords = re.findall(r'"([^"]+)"', user_message)
    if not keywords:
        for prep in ["about", "on", "regarding", "related to", "for"]:
            idx = msg.find(prep + " ")
            if idx != -1:
                snippet = user_message[idx + len(prep) + 1:].split()[:4]
                if snippet:
                    keywords = [" ".join(snippet)]
                break
    for kw in keywords[:2]:
        results = search_videos(text_query=kw, limit=5)
        if results:
            context_parts.append(f'**YouTube search results for "{kw}":**\n\n' + _fmt_videos(results, 5))
        else:
            context_parts.append(f'No YouTube videos found matching "{kw}".')

    # ── channel overview / stats / analytics ──────────────────────────────
    if any(w in msg for w in ["channel", "stat", "overview", "summary", "analytics", "dashboard"]):
        stats = get_channel_stats()
        lines = [f"• {ch}: {cnt} videos" for ch, cnt in stats.items()]
        context_parts.append("**Live channel overview (YouTube Data API):**\n" + "\n".join(lines))

    # ── default: show recent videos ───────────────────────────────────────
    if not context_parts:
        vids = get_recent_videos(limit=8)
        context_parts.append("**🔴 Live — latest videos streamed from YouTube right now:**\n\n" + _fmt_videos(vids, 8))

    db_context = "\n\n".join(context_parts)

    # ── Optional Gemini polish ────────────────────────────────────────────
    if _gemini_client:
        try:
            prompt = (
                f'You are a YouTube analytics assistant for a real-time cloud pipeline. The user asked: "{user_message}"\n\n'
                f"Here is the live data fetched from the YouTube Data API via our webhook pipeline:\n{db_context}\n\n"
                "Write a concise, well-formatted markdown answer using ONLY the data above. "
                "Always frame this as real-time live data fetched from YouTube. "
                "Never mention 'database', 'cache', or 'saved'. Use language like 'live feed', 'real-time', 'fetched from YouTube', 'ingested via webhook'. "
                "Be friendly and informative."
            )
            resp = _gemini_client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
            )
            text = getattr(resp, "text", None)
            if text and len(text.strip()) > 20:
                return text.strip()
        except Exception:
            pass  # fall through to plain answer

    return f"📡 **Live from YouTube pipeline:**\n\n{db_context}"

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN UI LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════

# Header
col1, col2 = st.columns([0.9, 0.1])
with col1:
    st.markdown("# 🎬 YouTube Intelligence Hub")
    st.markdown("*🔴 Live YouTube analytics powered by webhook pipeline & Google Gemini AI*")
with col2:
    st.markdown("")
    st.markdown("")
    if st.button("🔄", help="Refresh data"):
        st.rerun()

st.divider()

# Navigation
selected = option_menu(
    menu_title=None,
    options=["🤖 Chat Assistant", "📊 Analytics", "🎥 Videos", "⚙️ Settings"],
    icons=["chat-dots-fill", "bar-chart-fill", "film", "gear-fill"],
    orientation="horizontal",
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: CHAT ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════════
if selected == "🤖 Chat Assistant":
    st.subheader("AI Chatbot - Ask anything about YouTube videos!")
    
    # Example prompts
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📈 How many videos from Bloomberg?"):
            st.session_state.pending_query = "How many videos from Bloomberg Markets channel have we saved?"
            st.rerun()
    with col2:
        if st.button("🌍 USA videos in last 24h"):
            st.session_state.pending_query = "Give me a count of videos published about USA in ANI News India channel in the last 24 hours"
            st.rerun()
    with col3:
        if st.button("📊 Popular videos"):
            st.session_state.pending_query = "What are the most popular videos by view count?"
            st.rerun()
    
    st.markdown("---")

    # Process a pending query triggered by button click
    if st.session_state.pending_query:
        query = st.session_state.pending_query
        st.session_state.pending_query = None
        st.session_state.messages.append({"role": "user", "content": query})
        with st.spinner("🔴 Fetching live data from YouTube API..."):
            answer = _query_and_answer(query)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask me about YouTube videos...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)
        
        # Get AI response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔴 Fetching live data from YouTube API..."):
                response = _query_and_answer(user_input)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
elif selected == "📊 Analytics":
    try:
        st.subheader("📊 YouTube Channel Analytics")
        
        # Get stats
        col1, col2, col3, col4 = st.columns(4)
        
        collection = get_videos_collection()
        total_videos = collection.count_documents({})
        
        with col1:
            st.metric("📊 Total Videos", total_videos, delta=None)
        
        with col2:
            bloomberg_count = count_videos_by_channel("Bloomberg")
            st.metric("📺 Bloomberg Videos", bloomberg_count)
        
        with col3:
            ani_count = count_videos_by_channel("ANI News India")
            st.metric("🇮🇳 ANI News Videos", ani_count)
        
        with col4:
            videos_24h = len(get_videos_last_24h())
            st.metric("⏰ Last 24h", videos_24h)
        
        st.divider()
        
        # Popular videos
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.markdown("### 🔥 Top 10 Most Viewed Videos")
            popular = get_top_videos(limit=10)
            if popular:
                df_popular = pd.DataFrame([
                    {
                        "Title": v.get("title", "N/A")[:50] + "...",
                        "Views": f"{v.get('view_count', 0):,}",
                        "Likes": f"{v.get('like_count', 0):,}",
                        "Channel": v.get("channel") or v.get("channel_id") or "N/A"
                    }
                    for v in popular
                ])
                st.dataframe(df_popular, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("### 📊 Videos by Channel")
            try:
                stats = get_channel_stats()
                if stats:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=list(stats.keys()),
                            y=list(stats.values()),
                            marker_color=['#3b82f6', '#ef4444'],
                        )
                    ])
                    fig.update_layout(
                        height=350,
                        template="plotly_dark",
                        showlegend=False,
                        margin=dict(l=0, r=0, t=20, b=0),
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except:
                st.info("No channel data available yet")
        
        st.divider()
        
        # Recently added
        st.markdown("### 🔴 Live Feed — Latest Videos from YouTube")
        recent = get_recent_videos(limit=10)
        if recent:
            for i, video in enumerate(recent[:10], 1):
                with st.expander(f"🎥 {i}. {video.get('title', 'No title')[:60]}..."):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Description:** {video.get('description', 'N/A')[:200]}...")
                        st.write(f"**Channel:** {video.get('channel') or video.get('channel_id') or 'N/A'}")
                        st.write(f"**Uploaded:** {video.get('upload_date', 'N/A')}")
                    with col2:
                        st.metric("👁️ Views", f"{video.get('view_count', 0):,}")
                        st.metric("👍 Likes", f"{video.get('like_count', 0):,}")
        
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: VIDEOS BROWSER
# ═══════════════════════════════════════════════════════════════════════════════
elif selected == "🎥 Videos":
    st.subheader("🎥 Video Browser")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("🔍 Search videos...", placeholder="Enter keyword")
    
    with col2:
        channel_filter = st.selectbox(
            "📺 Filter by channel",
            ["All Channels", "Bloomberg", "ANI News India"]
        )
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Most Recent", "Most Viewed", "Most Liked"])
    
    st.divider()
    
    # Get videos
    try:
        if search_query:
            videos = search_videos(text_query=search_query, limit=20)
        elif channel_filter != "All Channels":
            videos = get_videos_by_channel(channel_filter, limit=20)
        else:
            videos = get_recent_videos(limit=20)
        
        if not videos:
            st.info("No videos found matching your criteria")
        else:
            # Sort
            if sort_by == "Most Viewed":
                videos = sorted(videos, key=lambda x: x.get("view_count", 0), reverse=True)
            elif sort_by == "Most Liked":
                videos = sorted(videos, key=lambda x: x.get("like_count", 0), reverse=True)
            
            # Display
            for i, video in enumerate(videos[:20], 1):
                vid_id  = video.get('video_id', '')
                url     = video.get('url') or f"https://www.youtube.com/watch?v={vid_id}"
                channel = video.get('channel') or video.get('channel_id') or 'N/A'
                st.markdown(f"""
                **{i}. {video.get('title', 'No title')}**

                🔗 [Watch on YouTube]({url})
                
                📺 **Channel:** {channel} | 👁️ **Views:** {video.get('view_count', 0):,} | 👍 **Likes:** {video.get('like_count', 0):,}
                
                📅 **Uploaded:** {video.get('upload_date', 'N/A')}
                """)
                st.caption(f"_{video.get('description', 'No description')[:150]}..._")
                st.divider()
    
    except Exception as e:
        st.error(f"Error loading videos: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif selected == "⚙️ Settings":
    st.subheader("⚙️ Settings & Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📡 System Status")
        try:
            collection = get_videos_collection()
            status = "✅ Connected"
            count = collection.count_documents({})
            st.success(f"{status}")
            st.metric("Videos Ingested via Webhook", count)
            st.info("Backend: **MongoDB Atlas** · YouTube Data API v3 · PubSubHubbub")
        except Exception as e:
            st.error(f"Connection Error: {e}")
    
    with col2:
        st.markdown("### 🔑 API Configuration")
        if st.session_state.api_key:
            st.success("✅ Google API configured")
            if st.button("Clear API Key"):
                st.session_state.api_key = ""
                st.rerun()
        else:
            st.warning("⚠️ Google API key not configured — add GOOGLE_API_KEY to .env")
    
    st.divider()
    
    st.markdown("### 📚 About")
    st.info("""
    **YouTube Intelligence Hub** is a production-ready AI-powered analytics platform that:
    
    - 🎬 Captures real-time YouTube video publications via webhooks
    - 💾 Stores metadata in MongoDB with intelligent schema
    - 🤖 Provides agentic AI chatbot powered by Google Gemini
    - 📊 Offers advanced analytics and video browsing
    - 🚀 Deployed as serverless functions on Google Cloud
    
    **Features:**
    - Agent-based AI with tool access to database
    - Real-time data ingestion (no polling)
    - RESTful API with authentication
    - Beautiful, responsive Streamlit UI
    """)
    
    st.divider()
    st.markdown("""
    **Built with:** Python, FastAPI, MongoDB, Google Generative AI, Streamlit
    
    **Version:** 1.0.0
    """)

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.85rem;">
    🚀 YouTube Intelligence Hub | Made with ❤️ for CloudNative AI Data Engineers
</div>
""", unsafe_allow_html=True)
