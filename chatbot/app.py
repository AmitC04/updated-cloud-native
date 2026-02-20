"""
chatbot/app.py
Streamlit app for the AI chatbot interface
"""
import streamlit as st
import os
from agents import get_chat_response

# Set page config
st.set_page_config(
    page_title="YouTube Video AI Assistant",
    page_icon="📺",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("🤖 AI Assistant Settings")
    st.markdown("""
    This AI assistant can answer questions about YouTube video data.
    
    **Capabilities:**
    - Query video statistics
    - Find videos by topic/channel
    - Get recommendations
    - Analyze trends
    """)
    
    st.divider()
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Main content
st.title("📺 YouTube Video AI Assistant")
st.caption("Ask questions about YouTube video data using natural language")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about YouTube videos, channels, or statistics..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown(" Thinking...")
        
        try:
            response = get_chat_response(prompt, st.session_state.messages[:-1])
            message_placeholder.markdown(response)
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            message_placeholder.markdown(error_msg)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response if 'response' in locals() else error_msg})

# Footer
st.divider()
st.markdown("*Powered by Google Gemini API and YouTube video data*")