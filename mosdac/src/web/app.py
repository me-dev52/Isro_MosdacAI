"""
Streamlit Web Interface for MOSDAC AI Help Bot
"""

import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="MOSDAC AI Help Bot",
    page_icon="🚀",
    layout="wide"
)

# Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_connection():
    """Check if API is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_query(query: str):
    """Send query to API"""
    try:
        payload = {"query": query}
        response = requests.post(f"{API_BASE_URL}/query", json=payload, timeout=30)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    """Main application function"""
    
    # Header
    st.title("🚀 MOSDAC AI Help Bot")
    st.markdown("Intelligent Virtual Assistant for Information Retrieval from MOSDAC Portal")
    
    # Check API connection
    if not check_api_connection():
        st.error("❌ Cannot connect to AI Help Bot API. Please ensure the backend is running on localhost:8000")
        st.info("To start the backend, run: `cd src/api && uvicorn main:app --reload`")
        return
    
    st.success("✅ Connected to AI Help Bot API")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Controls")
        
        if st.button("🔄 Refresh"):
            st.rerun()
            
        if st.button("📊 System Status"):
            try:
                response = requests.get(f"{API_BASE_URL}/status")
                if response.status_code == 200:
                    status = response.json()
                    st.json(status)
            except:
                st.error("Failed to get system status")
    
    # Main chat interface
    st.header("💬 Chat with AI Help Bot")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Chat input
    user_query = st.text_input(
        "Ask me anything about MOSDAC:",
        placeholder="e.g., What satellite data is available for Mumbai region?"
    )
    
    if st.button("🚀 Send") and user_query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        # Get AI response
        with st.spinner("🤖 AI is thinking..."):
            response = send_query(user_query)
            
            if response.get("success"):
                bot_message = response.get("response", "No response generated")
                st.session_state.messages.append({"role": "assistant", "content": bot_message, "data": response})
            else:
                error_msg = f"Error: {response.get('error', 'Unknown error')}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.rerun()
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"**👤 You:** {message['content']}")
        else:
            st.markdown(f"**🤖 AI:** {message['content']}")
            
            # Show additional info if available
            if "data" in message:
                with st.expander("📋 Response Details"):
                    data = message["data"]
                    
                    # Query Analysis
                    if "query_analysis" in data:
                        st.write("**Query Analysis:**")
                        analysis = data["query_analysis"]
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"Intent: {analysis.get('intent', 'Unknown')}")
                        with col2:
                            st.write(f"Confidence: {analysis.get('confidence', 0):.2f}")
                    
                    # Sources
                    if data.get("sources"):
                        st.write("**Sources:**")
                        for source in data["sources"]:
                            st.write(f"- {source.get('title', 'Unknown')} ({source.get('type', 'Unknown')})")
                    
                    # Suggestions
                    if data.get("suggestions"):
                        st.write("**Suggestions:**")
                        for suggestion in data["suggestions"]:
                            st.write(f"💡 {suggestion}")
    
    # Example queries
    if not st.session_state.messages:
        st.info("💡 **Try these example queries:**")
        
        examples = [
            "What satellite data is available for Mumbai region?",
            "How do I download satellite imagery?",
            "What is the spatial resolution of the data?",
            "How do I use the MOSDAC API?"
        ]
        
        for example in examples:
            if st.button(example, key=example):
                st.session_state.messages.append({"role": "user", "content": example})
                st.rerun()

if __name__ == "__main__":
    main()
