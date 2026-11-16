import streamlit as st
import uuid
import requests
import json
import sys
from pathlib import Path

# Add project root to sys.path so direct service fallback works seamlessly
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import get_settings
from app.services.chat_service import ChatService
from app.services.memory_service import MemoryService

# Page Configuration
st.set_page_config(
    page_title="Internship Application Agent - AI Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished, professional enterprise aesthetic
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #DBEAFE;
        color: #1D4ED8;
        margin-right: 0.4rem;
        margin-top: 0.3rem;
    }
    .source-box {
        background-color: #F8FAFC;
        border-left: 3px solid #3B82F6;
        padding: 0.6rem 0.8rem;
        border-radius: 4px;
        margin-top: 0.5rem;
        font-size: 0.85rem;
    }
    .stChatMessage {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

API_BASE_URL = "http://127.0.0.1:8000"

# Session State Initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am your AI product assistant for the **Internship Application Agent**. Ask me anything about how the platform works, resume upload and parsing, semantic internship matching, cover letter generation, interview preparation, or application tracking!",
            "sources": []
        }
    ]

# Backend Communication Functions
def check_backend_health():
    try:
        res = requests.get(f"{API_BASE_URL}/health", timeout=1.5)
        if res.status_code == 200:
            return True, res.json()
    except Exception:
        pass
    return False, None

def send_chat_message(session_id: str, question: str):
    backend_alive, _ = check_backend_health()
    if backend_alive:
        try:
            res = requests.post(
                f"{API_BASE_URL}/api/v1/chat",
                json={"session_id": session_id, "question": question},
                timeout=30
            )
            if res.status_code == 200:
                data = res.json()
                return data["answer"], data.get("sources", [])
        except Exception as e:
            st.error(f"API Error: {e}. Falling back to direct service.")

    # Direct In-Process Service Fallback
    chat_svc = ChatService()
    from app.schemas.chat import ChatRequest
    resp = chat_svc.handle_chat(ChatRequest(session_id=session_id, question=question))
    return resp.answer, resp.sources

def clear_session_memory(session_id: str):
    backend_alive, _ = check_backend_health()
    if backend_alive:
        try:
            requests.post(f"{API_BASE_URL}/api/v1/chat/clear", json={"session_id": session_id}, timeout=3)
        except Exception:
            pass
    MemoryService().clear_session(session_id)


# Sidebar Configuration
with st.sidebar:
    st.title("💼 Platform Controls")
    
    backend_online, health_info = check_backend_health()
    if backend_online:
        st.success("🟢 API Server: Online (Port 8000)")
    else:
        st.info("🔵 Engine: Direct In-Process Mode")

    st.markdown("---")
    st.markdown(f"**Current Session ID:**\n`{st.session_state.session_id}`")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ New Session", use_container_width=True):
            st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Started a new conversation session. How can I help you with the Internship Application Agent?",
                    "sources": []
                }
            ]
            st.rerun()

    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            clear_session_memory(st.session_state.session_id)
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Conversation history cleared. Ready for your questions!",
                    "sources": []
                }
            ]
            st.rerun()

    st.markdown("---")
    st.subheader("💡 Suggested Prompts")
    examples = [
        "What is this product and how does it work?",
        "Can you explain the process step by step?",
        "How can I upload my resume?",
        "How does internship matching work?",
        "What about the score?",
        "How can I generate a cover letter?",
        "What is the interview preparation feature?",
        "Tell me the latest cricket score."
    ]

    for ex in examples:
        if st.button(ex, key=f"btn_{ex}", use_container_width=True):
            st.session_state.pending_prompt = ex
            st.rerun()

    st.markdown("---")
    st.markdown("""
    **Core Capabilities:**
    - 📄 Resume Upload & Text Extraction
    - 🔍 Semantic Similarity Matching
    - ✍️ Tailored Cover Letter Generator
    - 🎯 STAR Method Interview Prep
    - 📊 Kanban Application Tracker
    - 🧠 Persistent Memory & Follow-up Resolution
    """)


# Main Chat Interface
st.markdown('<div class="main-header">Internship Application Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI Product Assistant & Documentation Copilot (Infosys Springboard 7.0)</div>', unsafe_allow_html=True)

# Render Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📚 Verified Sources Cited", expanded=False):
                for src in message["sources"]:
                    st.markdown(f'<span class="badge">📄 {src}</span>', unsafe_allow_html=True)

# Handle Pending Prompt or User Input
prompt_to_process = None
if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt_to_process = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
else:
    user_input = st.chat_input("Ask a question about the Internship Application Agent...")
    if user_input:
        prompt_to_process = user_input

if prompt_to_process:
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": prompt_to_process})
    with st.chat_message("user"):
        st.markdown(prompt_to_process)

    # 2. Generate Assistant Response with Loading Spinner
    with st.chat_message("assistant"):
        with st.spinner("Searching product knowledge base and formulating grounded answer..."):
            answer, sources = send_chat_message(st.session_state.session_id, prompt_to_process)
            st.markdown(answer)
            if sources:
                with st.expander("📚 Verified Sources Cited", expanded=True):
                    for src in sources:
                        st.markdown(f'<span class="badge">📄 {src}</span>', unsafe_allow_html=True)

    # 3. Save to Session State
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })
