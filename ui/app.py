import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from dotenv import load_dotenv
from rag.engine import RAGEngine

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Quant MF Assistant",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def init_engine():
    """Initialize the RAG engine and handle missing keys (Edge Case 5.A.1)"""
    if "engine" not in st.session_state:
        if not os.getenv("GROQ_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            st.error("🚨 **API Keys Missing!**\nPlease add your `GROQ_API_KEY` or `GEMINI_API_KEY` to the `.env` file located at the root of the project to start the assistant.")
            st.stop()
        
        try:
            st.session_state.engine = RAGEngine()
        except Exception as e:
            st.error(f"Failed to initialize engine: {e}")
            st.stop()

def main():
    st.title("📈 Quant Mutual Fund Assistant")
    
    # Disclaimer Banner (Phase 5.C)
    st.caption("⚠️ **Facts-only. No investment advice.** I can only answer factual questions based on official scheme documents.")
    
    init_engine()

    # Initialize chat history (Phase 5.B)
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
        # Welcome message with examples (Phase 5.A)
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Welcome! I can answer factual questions about the Quant Mutual Fund schemes. Try asking:\n\n"
                       "- 💡 *What is the expense ratio of Quant Small Cap Fund?*\n"
                       "- 💡 *Who is the fund manager for ELSS?*\n"
                       "- 💡 *What is the exit load for Quant Multi Asset?*"
        })

    # Render previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask a factual question about Quant Mutual Funds..."):
        
        # Edge Case 5.B.1: Handle empty inputs (Streamlit chat_input handles this automatically, but just in case)
        if not prompt.strip():
            return
            
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response
        with st.chat_message("assistant"):
            # Edge Case 5.B.2: Show spinner to handle lag
            with st.spinner("Searching official documents..."):
                response = st.session_state.engine.query(prompt)
                
                # Render the response (markdown naturally supports the clickable citations we built in Phase 3.C)
                st.markdown(response)
                
        # Store response
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
