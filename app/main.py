"""1421 AI - Historical Research System
Professional version with analytics, saved searches, and feedback
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import json
import re
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import threading
import random
import os
from collections import Counter
import requests
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from googlesearch import search as google_search
import openai

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="1421 AI - Historical Research System",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== INITIALIZE SESSION STATE ==========
DEFAULT_ANALYTICS = {
    'total_searches': 0, 'searches_by_day': {}, 'searches_by_hour': {},
    'questions_asked': [], 'response_times': [], 'popular_topics': {},
    'user_sessions': [], 'sources_used': {'documents': 0, 'web': 0, 'both': 0}
}

DEFAULT_STATE = {
    'search_analytics': DEFAULT_ANALYTICS,
    'saved_searches': [],
    'current_page': 'dashboard',
    'current_question': '',
    'auto_search': False,
    'chat_history': [],
    'deleting_search_id': None,
    'feedback_submitted': False,
    'animation_playing': False,
    'current_year': 1368,
    'map_data': None,
    'search_mode': 'Auto (Documents + Web)',
    'saved_sidebar_collapsed': False,
    'chat_sessions': [],  # For multiple chat sessions like DeepSeek
    'current_chat_id': 0
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Initialize default chat session
if not st.session_state.chat_sessions:
    st.session_state.chat_sessions = [{
        'id': 0,
        'name': 'New Chat',
        'history': [],
        'created': datetime.now().strftime("%Y-%m-%d %H:%M")
    }]

# ========== CSS STYLING ==========
st.markdown("""
<style>
/* Main styling */
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
.main .block-container { background: rgba(255,255,255,0.98); border-radius: 15px; padding: 2rem; margin-top: 1rem; box-shadow: 0 6px 20px rgba(0,0,0,0.1); max-width: 1200px; margin-left: auto; margin-right: auto; }

/* Headers */
.main-header { font-size: 2.8rem; color: #000; text-align: center; margin-bottom: 0.5rem; font-weight: 800; background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.sub-header { font-size: 1.8rem; color: #2c3e50; margin-bottom: 1.5rem; font-weight: 700; border-bottom: 3px solid #d4af37; padding-bottom: 0.5rem; }

/* Main layout - Two column for chat sidebar and content */
.main-layout {
    display: flex;
    gap: 20px;
}

/* Chat sidebar - Right side like DeepSeek */
.chat-sidebar {
    background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%);
    border-left: 4px solid #d4af37;
    padding: 1.5rem 1rem;
    height: calc(100vh - 100px);
    position: sticky;
    top: 10px;
    right: 0;
    border-radius: 12px 0 0 12px;
    color: white;
    overflow-y: auto;
    width: 280px;
    flex-shrink: 0;
}

.chat-sidebar.collapsed {
    width: 60px;
    padding: 1.5rem 0.5rem;
}

.chat-sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(212,175,55,0.3);
}

.new-chat-btn {
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
    color: black;
    border: none;
    border-radius: 8px;
    padding: 10px 15px;
    font-weight: 600;
    width: 100%;
    cursor: pointer;
    margin-bottom: 20px;
    transition: all 0.3s ease;
}

.new-chat-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

.chat-session-item {
    background: rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    border-left: 3px solid transparent;
    cursor: pointer;
    transition: all 0.3s ease;
}

.chat-session-item:hover {
    background: rgba(255,255,255,0.2);
    border-left: 3px solid #d4af37;
}

.chat-session-item.active {
    background: rgba(212,175,55,0.2);
    border-left: 3px solid #d4af37;
}

.chat-session-name {
    font-size: 0.95rem;
    color: white;
    font-weight: 600;
    margin-bottom: 4px;
}

.chat-session-time {
    font-size: 0.7rem;
    color: #ccc;
}

/* Left Navigation Sidebar */
section[data-testid="stSidebar"] > div { 
    background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%) !important; 
    border-right: 4px solid #d4af37;
    padding-top: 1.2rem !important;
}

/* Navigation buttons - larger text, closer together */
.stSidebar .stButton > button {
    background: transparent;
    color: white !important;
    border: none !important;
    border-radius: 6px;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    padding: 10px 14px !important;
    margin: 2px 0 !important;
    text-align: left;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.2s ease;
    width: 100%;
}

.stSidebar .stButton > button:hover {
    background: rgba(212,175,55,0.2) !important;
    transform: translateX(3px);
    border-left: 3px solid #d4af37 !important;
}

.stSidebar .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%) !important;
    color: #000 !important;
    font-weight: 700 !important;
}

/* Source badges */
.source-badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; margin-right: 8px; margin-bottom: 8px; }
.badge-document { background: #4a6491; color: white; }
.badge-web { background: #28a745; color: white; }

/* Metrics */
[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; color: #2c3e50 !important; }
[data-testid="stMetricLabel"] { font-weight: 600 !important; font-size: 1rem !important; color: #d4af37 !important; }

/* Saved searches in right sidebar */
.saved-search-sidebar-item { background: rgba(255,255,255,0.1); border-radius: 8px; padding: 12px; margin: 8px 0; border-left: 4px solid #d4af37; cursor: pointer; transition: all 0.3s ease; }
.saved-search-sidebar-item:hover { background: rgba(255,255,255,0.2); transform: translateX(5px); }
.search-time { font-size: 0.8rem; color: #ccc; margin-top: 5px; }
.search-query { font-size: 0.9rem; color: #fff; margin-bottom: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Yellow text for no saved searches */
.no-saved-searches { background: rgba(255,255,255,0.1); border-radius: 8px; padding: 15px; margin: 10px 0; text-align: center; color: #FFD700 !important; font-style: italic; }
.no-saved-searches small { color: #FFD700 !important; }

/* Answer display with typing animation */
.answer-text { 
    font-size: 1.1rem; 
    line-height: 1.8; 
    color: #2c3e50; 
    margin: 20px 0; 
    padding: 10px 0; 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}
.typing-animation { border-right: 2px solid #d4af37; animation: blink 1s step-end infinite; white-space: pre-wrap; }
@keyframes blink { from, to { border-color: transparent; } 50% { border-color: #d4af37; } }

.chat-message { padding: 20px; margin: 15px 0; border-radius: 12px; max-width: 100%; animation: fadeIn 0.3s ease; }
.user-message { background: linear-gradient(135deg, #4a6491 0%, #2c3e50 100%); color: white; margin-right: 20%; border-bottom-right-radius: 4px; }
.assistant-message { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); color: #333; border: 1px solid #ddd; margin-left: 20%; border-bottom-left-radius: 4px; }

/* Query text styling - same as assistant message */
.assistant-message .answer-text, 
.assistant-message p,
.assistant-message strong,
.assistant-message em {
    color: #2c3e50;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}

/* Action buttons */
.action-buttons { display: flex; gap: 10px; margin-top: 15px; margin-bottom: 20px; }
.copy-button, .save-button { background: linear-gradient(135deg, #6c757d 0%, #495057 100%); color: white; border: none; border-radius: 6px; padding: 8px 16px; font-size: 0.9rem; cursor: pointer; }
.save-button { background: linear-gradient(135deg, #4a6491 0%, #2c3e50 100%); }
.copy-button:hover, .save-button:hover { transform: translateY(-2px); }

/* Delete button */
.delete-button { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; border: none; border-radius: 6px; padding: 4px 8px; font-size: 0.8rem; cursor: pointer; }

/* Headers */
.saved-searches-header, .system-status-header { color: #FFD700 !important; font-weight: 700 !important; }

/* Question input at bottom - DeepSeek style, fixed at bottom */
.question-input-container {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: min(800px, 90%);
    background: white;
    padding: 15px 20px;
    border: 1px solid #e0e0e0;
    border-radius: 50px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    z-index: 1000;
    display: flex;
    align-items: center;
    backdrop-filter: blur(10px);
    background: rgba(255,255,255,0.95);
}

.question-input-container textarea {
    border: none;
    background: transparent;
    padding: 10px 15px;
    font-size: 1rem;
    resize: none;
    outline: none;
    flex-grow: 1;
}

.question-input-container button {
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
    color: white;
    border: none;
    border-radius: 30px;
    padding: 10px 24px;
    font-weight: 600;
    margin-left: 10px;
    white-space: nowrap;
}

/* Confirmation dialog */
.confirmation-dialog { background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px; margin: 10px 0; color: #856404; }

/* Map container */
.map-container { margin-bottom: 100px; }

/* Timeline controls */
.timeline-controls { 
    display: flex; 
    gap: 10px; 
    align-items: center; 
    margin: 15px 0; 
    padding: 15px; 
    background: #f8f9fa; 
    border-radius: 8px; 
}

/* Hide default title */
.js-plotly-plot .gtitle { display: none; }

/* Content area with margin for bottom fixed input */
.content-area {
    margin-bottom: 100px;
    padding-bottom: 20px;
}

/* Document search - full width */
.document-search-container {
    width: 100%;
    margin-bottom: 20px;
}

.document-search-input {
    width: 100%;
    padding: 12px 18px;
    border: 2px solid #e0e0e0;
    border-radius: 30px;
    font-size: 1rem;
    transition: all 0.3s ease;
}

.document-search-input:focus {
    border-color: #d4af37;
    box-shadow: 0 0 0 3px rgba(212,175,55,0.1);
    outline: none;
}

/* UK English text */
p, div, span, li {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}

/* Toggle sidebar button */
.toggle-sidebar-btn {
    background: transparent;
    color: white;
    border: 1px solid #d4af37;
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 0.8rem;
    cursor: pointer;
}

.toggle-sidebar-btn:hover {
    background: rgba(212,175,55,0.2);
}
</style>

<script>
function copyAnswerToClipboard(t) { navigator.clipboard.writeText(t).then(()=>alert('Answer copied to clipboard!'), e=>console.error(e)); }

// Typing animation effect
function typeWriter(elementId, text, speed = 20) {
    let i = 0;
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.innerHTML = '';
    element.classList.add('typing-animation');
    
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        } else {
            element.classList.remove('typing-animation');
        }
    }
    type();
}

// Auto-scroll to bottom
function scrollToBottom() {
    window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
    });
}

// Toggle sidebar
function toggleChatSidebar() {
    const sidebar = document.querySelector('.chat-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
    }
}
</script>
""", unsafe_allow_html=True)

# ========== THREAD-SAFE DATABASE ==========
class ThreadSafeDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.local = threading.local()
    
    def get_connection(self):
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
    
    def execute(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        return cursor

# ========== WEB SEARCH MODULE ==========
class WebSearchModule:
    def __init__(self):
        self.openai_client = None
        try:
            if 'OPENAI_API_KEY' in st.secrets:
                self.openai_client = openai.OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
            elif 'OPENAI_API_KEY' in os.environ:
                self.openai_client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        except:
            self.openai_client = None
    
    def search_google(self, query: str, limit: int = 3) -> List[Dict]:
        try:
            results = []
            for url in list(google_search(query, num_results=limit, lang='en'))[:limit]:
                try:
                    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                    soup = BeautifulSoup(r.content, 'html.parser')
                    title = (soup.title.string if soup.title else "Web Page")[:150]
                    snippet = ""
                    for p in soup.find_all('p'):
                        if len(p.text.strip()) > 100:
                            snippet = p.text[:300] + "..."
                            break
                    if not snippet:
                        meta = soup.find('meta', attrs={'name': 'description'})
                        snippet = meta['content'][:300] + "..." if meta and meta.get('content') else f"Content about {query}"
                    results.append({'title': title, 'snippet': snippet, 'url': url, 'source': 'web'})
                except:
                    results.append({'title': f"Web Result", 'snippet': f"Web page about {query}", 'url': url, 'source': 'web'})
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

# ========== SAVED SEARCHES SYSTEM ==========
class SavedSearchesSystem:
    @staticmethod
    def save_search(question, answer, sources, doc_results, web_results):
        entry = {
            'id': len(st.session_state.saved_searches) + 1,
            'question': question, 'answer': answer, 'sources': sources,
            'document_results_count': len(doc_results), 'web_results_count': len(web_results),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'time': datetime.now().strftime("%H:%M"),
            'document_results': doc_results[:3], 'web_results': web_results[:2]
        }
        st.session_state.saved_searches.append(entry)
        return entry
    
    @staticmethod
    def delete_search(search_id):
        st.session_state.saved_searches = [s for s in st.session_state.saved_searches if s['id'] != search_id]
    
    @staticmethod
    def render_chat_sidebar():
        """Render the right sidebar with chat sessions and saved searches (DeepSeek style)"""
        saved = st.session_state.saved_searches
        chat_sessions = st.session_state.chat_sessions
        current_id = st.session_state.current_chat_id
        
        # Chat sidebar container
        st.markdown("""
        <div class="chat-sidebar">
            <div class="chat-sidebar-header">
                <h3 style="color: #d4af37; margin:0;">Chat History</h3>
                <button class="toggle-sidebar-btn" onclick="toggleChatSidebar()">◀</button>
            </div>
        """, unsafe_allow_html=True)
        
        # New Chat button
        if st.button("+ New Chat", key="new_chat_btn", use_container_width=True):
            new_id = len(chat_sessions)
            st.session_state.chat_sessions.append({
                'id': new_id,
                'name': f'Chat {new_id + 1}',
                'history': [],
                'created': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.session_state.current_chat_id = new_id
            st.rerun()
        
        # Chat sessions
        st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
        for session in chat_sessions[-5:][::-1]:  # Show last 5
            active_class = "active" if session['id'] == current_id else ""
            st.markdown(f"""
            <div class="chat-session-item {active_class}" onclick="document.getElementById('chat_{session['id']}').click();">
                <div class="chat-session-name">{session['name']}</div>
                <div class="chat-session-time">{session['created'][:10]}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Select", key=f"chat_{session['id']}", help="Select this chat"):
                st.session_state.current_chat_id = session['id']
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: rgba(212,175,55,0.3); margin: 20px 0;'>", unsafe_allow_html=True)
        
        # Saved searches section
        st.markdown('<h3 class="saved-searches-header">SAVED SEARCHES</h3>', unsafe_allow_html=True)
        
        if saved:
            for s in saved[-5:][::-1]:
                cols = st.columns([3, 1, 1])
                with cols[0]:
                    st.markdown(f'<div class="saved-search-sidebar-item"><div class="search-query">{s["question"][:40]}{"..." if len(s["question"])>40 else ""}</div><div class="search-time">{s["time"]} • {len(s["sources"])} sources</div></div>', unsafe_allow_html=True)
                with cols[1]:
                    if st.button("↻", key=f"sr_{s['id']}", help="Reload this search"):
                        st.session_state.current_question = s['question']
                        st.session_state.auto_search = True
                        st.rerun()
                with cols[2]:
                    if st.button("🗑", key=f"sd_{s['id']}", help="Delete this search"):
                        st.session_state.deleting_search_id = s['id']
                        st.rerun()
            
            if st.session_state.deleting_search_id:
                st.markdown('<div class="confirmation-dialog"><strong>Delete Search?</strong><br><small>This action cannot be undone.</small></div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                if c1.button("Confirm", key="confirm_del"):
                    SavedSearchesSystem.delete_search(st.session_state.deleting_search_id)
                    st.session_state.deleting_search_id = None
                    st.rerun()
                if c2.button("Cancel", key="cancel_del"):
                    st.session_state.deleting_search_id = None
                    st.rerun()
            st.markdown(f"*Showing 5 of {len(saved)}*")
        else:
            st.markdown('<div class="no-saved-searches">No saved searches yet.<br><small>Searches are automatically saved.</small></div>', unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)  # Close chat-sidebar div

# ========== FEEDBACK SYSTEM ==========
class FeedbackSystem:
    @staticmethod
    def send_feedback(name: str, email: str, message: str, feedback_type: str):
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'name': name,
            'email': email,
            'message': message,
            'type': feedback_type
        }
        
        if 'feedback_history' not in st.session_state:
            st.session_state.feedback_history = []
        st.session_state.feedback_history.append(feedback)
        
        print(f"FEEDBACK: {feedback}")
        return True
    
    @staticmethod
    def render_feedback_page():
        st.markdown('<h2 class="sub-header">SEND FEEDBACK</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 30px; border-radius: 12px; margin: 20px 0;">
            <h3 style="color: #2c3e50; margin-bottom: 20px;">Help us improve 1421 AI</h3>
            <p style="color: #666; margin-bottom: 30px;">Your feedback helps us make the system better for everyone.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your Name", placeholder="Optional")
        with col2:
            email = st.text_input("Email Address", placeholder="Required")
        
        feedback_type = st.selectbox("Feedback Type", 
                                    ["Bug Report", "Feature Request", "Suggestion", "Question", "Other"])
        
        message = st.text_area("Your Message", placeholder="Please describe your issue, suggestion, or question in detail...", 
                              height=150)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("SUBMIT FEEDBACK", type="primary", use_container_width=True):
                if not email:
                    st.error("Email is required")
                elif not message:
                    st.error("Message is required")
                else:
                    if FeedbackSystem.send_feedback(name or "Anonymous", email, message, feedback_type):
                        st.success("Thank you for your feedback! We will review it shortly.")
                        st.session_state.feedback_submitted = True
                        time.sleep(2)
                        st.session_state.current_page = "dashboard"
                        st.rerun()
        
        with col3:
            if st.button("BACK TO DASHBOARD", use_container_width=True):
                st.session_state.current_page = "dashboard"
                st.rerun()

# ========== RESEARCH SYSTEM ==========
class ResearchSystem:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.db_path = self.base_dir / "data" / "knowledge_base.db"
        self.db = None
        self.web_searcher = WebSearchModule()
        self._initialize()
    
    def _initialize(self):
        try:
            if not self.db_path.exists():
                return False
            self.db = ThreadSafeDatabase(str(self.db_path))
            self.db.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Init error: {e}")
            return False
    
    def get_database_stats(self):
        if not self.db:
            return None
        try:
            total = self.db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            saved = len(st.session_state.saved_searches)
            return {'total_documents': total, 'saved_searches': saved, 'geocoded_locations': 25}
        except:
            return {'total_documents': 0, 'saved_searches': 0, 'geocoded_locations': 0}
    
    def get_all_documents(self, limit=None):
        if not self.db:
            return []
        try:
            q = "SELECT * FROM documents ORDER BY id"
            if limit:
                q += " LIMIT ?"
                rows = self.db.execute(q, (limit,) if limit else ()).fetchall()
            else:
                rows = self.db.execute(q).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def search_documents(self, query: str, limit: int = 10) -> List[Dict]:
        if not self.db or not query:
            return []
        try:
            clean = query.strip().lower().replace('?', '')
            words = [w for w in clean.split() if len(w) > 3][:3]
            if not words:
                words = clean.split()[:3]
            
            conditions = []
            params = []
            for w in words:
                p = f"%{w}%"
                conditions.append("(title LIKE ? OR content LIKE ?)")
                params.extend([p, p])
            
            q = f"SELECT * FROM documents WHERE {' OR '.join(conditions)} ORDER BY id LIMIT ?"
            params.append(limit * 2)
            
            docs = []
            seen = set()
            for row in self.db.execute(q, params).fetchall():
                d = dict(row)
                if d['id'] not in seen:
                    seen.add(d['id'])
                    content = d.get('content', '')
                    d['word_count'] = len(content.split()) if content else 0
                    
                    lower = content.lower()
                    snippet = ""
                    for w in words:
                        if w in lower:
                            idx = lower.find(w)
                            start = max(0, idx - 150)
                            end = min(len(content), idx + 250)
                            snippet = content[start:end] + "..."
                            break
                    if not snippet and content:
                        snippet = content[:300] + "..."
                    d['snippet'] = snippet
                    docs.append(d)
                    if len(docs) >= limit:
                        break
            return docs
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_map_locations(self):
        """Get geographical locations for map with timeline data"""
        locations = [
            {'name': 'Beijing', 'lat': 39.9042, 'lon': 116.4074, 'year': 1403, 'event': 'Capital moved to Beijing'},
            {'name': 'Nanjing', 'lat': 32.0603, 'lon': 118.7969, 'year': 1368, 'event': 'Early Ming capital established'},
            {'name': 'Calicut', 'lat': 11.2588, 'lon': 75.7804, 'year': 1406, 'event': 'Zheng He\'s fleet first arrived'},
            {'name': 'Sumatra', 'lat': -0.5897, 'lon': 101.3431, 'year': 1407, 'event': 'Strategic trading post established'},
            {'name': 'Java', 'lat': -7.6145, 'lon': 110.7123, 'year': 1407, 'event': 'Diplomatic missions conducted'},
            {'name': 'Malacca', 'lat': 2.1896, 'lon': 102.2501, 'year': 1409, 'event': 'Strategic port established'},
            {'name': 'Sri Lanka', 'lat': 7.8731, 'lon': 80.7718, 'year': 1409, 'event': 'Trilingual inscription erected'},
            {'name': 'Hormuz', 'lat': 27.1561, 'lon': 56.2815, 'year': 1414, 'event': 'Persian Gulf trade route opened'},
            {'name': 'Mombasa', 'lat': -4.0435, 'lon': 39.6682, 'year': 1418, 'event': 'East African trade commenced'},
            {'name': 'Zanzibar', 'lat': -6.1659, 'lon': 39.2026, 'year': 1419, 'event': 'Trade agreements established'},
            {'name': 'Aden', 'lat': 12.7855, 'lon': 45.0187, 'year': 1417, 'event': 'Arabian Peninsula contact made'},
            {'name': 'Mogadishu', 'lat': 2.0469, 'lon': 45.3182, 'year': 1418, 'event': 'Somali coast exploration'},
            {'name': 'Champa', 'lat': 10.8231, 'lon': 106.6297, 'year': 1405, 'event': 'Southeast Asian ally'},
            {'name': 'Siam', 'lat': 13.7367, 'lon': 100.5231, 'year': 1408, 'event': 'Diplomatic relations established'}
        ]
        
        timeline = [{'year': l['year'], 'location': l['name'], 'event': l['event']} for l in locations]
        timeline.sort(key=lambda x: x['year'])
        
        return {'locations': locations, 'timeline_events': timeline}
    
    def generate_intelligent_answer(self, question, doc_results, web_results, mode):
        """Generate a coherent, well-structured answer in UK English without copying verbatim"""
        sources = []
        
        if not doc_results and not web_results:
            return "I could not find specific information about that in our historical database or on the web. Please try rephrasing your question or using different keywords.", []
        
        # Determine which sources to use based on mode
        use_docs = mode in ['Auto (Documents + Web)', 'Documents Only']
        use_web = mode in ['Auto (Documents + Web)', 'Web Only']
        
        if use_docs and doc_results:
            sources.append('documents')
        if use_web and web_results:
            sources.append('web')
        
        # If no sources after filtering, fallback
        if not sources:
            return "No information available with current search settings. Please try changing your search mode.", []
        
        # Try OpenAI first for intelligent response
        if self.web_searcher.openai_client:
            try:
                doc_context = ""
                if use_docs and doc_results:
                    for d in doc_results[:3]:
                        title = d.get('title', 'Unknown')
                        content = d.get('snippet', d.get('content', ''))[:500]
                        doc_context += f"Document '{title}': {content}\n\n"
                
                web_context = ""
                if use_web and web_results:
                    for w in web_results[:3]:
                        title = w.get('title', 'Unknown')
                        content = w.get('snippet', '')[:500]
                        web_context += f"Web source '{title}': {content}\n\n"
                
                prompt = f"""You are a professional historian specialising in Chinese maritime exploration during the Ming dynasty. 
Answer the following question in clear, fluent UK English. Do not copy text verbatim from the sources. 
Instead, synthesise the information into a coherent, well-structured response with proper paragraphs.
Use British English spelling and conventions.

Question: {question}

Available information:
{doc_context}
{web_context}

Please provide a comprehensive answer that:
1. Directly addresses the question
2. Presents key facts and historical context
3. Uses professional academic tone
4. Does not include URLs or references in the main text
5. Is written in proper UK English
"""
                
                resp = self.web_searcher.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional historian specialising in early Chinese maritime exploration. You write in clear, academic UK English and synthesise information rather than copying it."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=700,
                    temperature=0.7
                )
                
                if resp and resp.choices:
                    answer = resp.choices[0].message.content
                    # Remove any URLs just in case
                    answer = re.sub(r'https?://\S+', '', answer)
                    return answer, sources
            except Exception as e:
                print(f"OpenAI generation failed: {e}")
        
        # Enhanced fallback with better synthesis
        key_points = []
        
        if use_docs and doc_results:
            for d in doc_results[:3]:
                content = d.get('snippet', d.get('content', ''))[:200]
                # Clean and summarise
                content = re.sub(r'#\S+', '', content)  # Remove hashtags
                content = re.sub(r'https?://\S+', '', content)  # Remove URLs
                content = ' '.join(content.split())  # Clean whitespace
                if len(content) > 50:
                    key_points.append(content)
        
        if use_web and web_results:
            for w in web_results[:2]:
                content = w.get('snippet', '')[:200]
                content = re.sub(r'https?://\S+', '', content)
                content = ' '.join(content.split())
                if len(content) > 50:
                    key_points.append(content)
        
        # Build a coherent response
        response_parts = []
        
        # Introduction
        intro_templates = [
            f"Regarding {question.lower().replace('?', '')}, historical evidence suggests several important conclusions.",
            f"The question of {question.lower().replace('?', '')} can be addressed through examination of available historical records.",
            f"Historical research into {question.lower().replace('?', '')} reveals a complex picture."
        ]
        response_parts.append(random.choice(intro_templates))
        
        # Body - synthesise key points
        if key_points:
            response_parts.append("\n\n" + key_points[0][:300])
            if len(key_points) > 1:
                response_parts.append("\n\nFurthermore, " + key_points[1][0].lower() + key_points[1][1:300] if key_points[1] else "")
            if len(key_points) > 2:
                response_parts.append("\n\nAdditional evidence indicates " + key_points[2][0].lower() + key_points[2][1:300] if key_points[2] else "")
        
        # Conclusion
        response_parts.append("\n\nThese findings demonstrate the significance of Chinese maritime exploration during this period, though further research continues to refine our understanding.")
        
        # Source attribution
        if len(sources) > 1:
            response_parts.append("\n\n**Sources:** This analysis draws from both historical documents and contemporary web research.")
        elif 'documents' in sources:
            response_parts.append("\n\n**Sources:** This analysis is primarily based on historical documents in the 1421 research database.")
        else:
            response_parts.append("\n\n**Sources:** This analysis draws from web-based historical research.")
        
        return ''.join(response_parts), sources
    
    def perform_search(self, question):
        start = time.time()
        mode = st.session_state.get('search_mode', 'Auto (Documents + Web)')
        
        # Search based on mode
        docs = []
        web = []
        
        if mode in ['Auto (Documents + Web)', 'Documents Only']:
            docs = self.search_documents(question, 10)
        
        if mode in ['Auto (Documents + Web)', 'Web Only']:
            # Only do web search if no docs found in Auto mode, or always in Web Only mode
            if mode == 'Web Only' or (mode == 'Auto (Documents + Web)' and not docs):
                time.sleep(0.3)
                web = self.web_searcher.search_google(question, 3)
        
        answer, sources = self.generate_intelligent_answer(question, docs, web, mode)
        
        # Track analytics
        a = st.session_state.search_analytics
        a['total_searches'] += 1
        today = datetime.now().strftime("%Y-%m-%d")
        a['searches_by_day'][today] = a['searches_by_day'].get(today, 0) + 1
        a['response_times'].append(time.time() - start)
        if len(a['response_times']) > 500:
            a['response_times'] = a['response_times'][-500:]
        
        # Track source usage
        if len(sources) > 1:
            a['sources_used']['both'] += 1
        elif 'documents' in sources:
            a['sources_used']['documents'] += 1
        elif 'web' in sources:
            a['sources_used']['web'] += 1
        
        return {
            'question': question, 'answer': answer, 'sources_used': sources,
            'document_results': docs, 'web_results': web,
            'total_results': len(docs) + len(web)
        }

# ========== PAGE FUNCTIONS ==========
def show_dashboard(system):
    # Get current chat history
    current_chat_id = st.session_state.current_chat_id
    current_session = next((s for s in st.session_state.chat_sessions if s['id'] == current_chat_id), None)
    
    if current_session:
        chat_history = current_session['history']
    else:
        chat_history = []
    
    st.markdown('<h2 class="sub-header">DASHBOARD</h2>', unsafe_allow_html=True)
    
    stats = system.get_database_stats()
    if stats:
        cols = st.columns(4)
        cols[0].metric("Total Documents", stats['total_documents'])
        cols[1].metric("Saved Searches", stats['saved_searches'])
        cols[2].metric("Geocoded Locations", stats['geocoded_locations'])
        cols[3].metric("Database Status", "Active" if system.db else "Inactive")
    
    st.divider()
    st.markdown('<h2 class="sub-header">ASK HISTORICAL QUESTIONS</h2>', unsafe_allow_html=True)
    
    # Example questions
    examples = [
        "What was the significance of Zheng He's voyages?",
        "Is there evidence of Chinese ships reaching America before Columbus?",
        "Describe Ming Dynasty naval technology and shipbuilding",
        "What were the main purposes of the Chinese treasure fleets?",
        "How did Chinese navigation compare to European methods?"
    ]
    cols = st.columns(2)
    for i, q in enumerate(examples):
        with cols[i % 2]:
            if st.button(q, key=f"ex_{i}", use_container_width=True):
                st.session_state.current_question = q
                st.session_state.auto_search = True
                st.rerun()
    
    st.divider()
    
    # Chat history for current session
    for idx, chat in enumerate(chat_history[-20:]):
        st.markdown(f'<div class="chat-message user-message"><strong>You:</strong><br>{chat["question"]}</div>', unsafe_allow_html=True)
        
        answer_id = f"answer_{idx}_{int(time.time())}"
        st.markdown(f'<div class="chat-message assistant-message"><strong>1421 AI:</strong><br><div id="{answer_id}" class="answer-text">{chat["answer"]}</div></div>', unsafe_allow_html=True)
        
        # Only trigger typing animation for the latest message
        if idx == len(chat_history[-20:]) - 1:
            st.markdown(f'<script>setTimeout(function() {{ typeWriter("{answer_id}", `{chat["answer"].replace("`", "\\`").replace(chr(10), "\\n")}`); scrollToBottom(); }}, 100);</script>', unsafe_allow_html=True)
        
        st.markdown(f'<div class="action-buttons"><button class="copy-button" onclick="copyAnswerToClipboard(`{chat["answer"].replace("`", "'").replace(chr(10), "\\n")}`)">Copy Answer</button></div>', unsafe_allow_html=True)
        
        st.markdown("**Sources used:**")
        if 'documents' in chat['sources_used']:
            st.markdown('<span class="source-badge badge-document">Documents</span>', unsafe_allow_html=True)
        if 'web' in chat['sources_used']:
            st.markdown('<span class="source-badge badge-web">Web</span>', unsafe_allow_html=True)
        
        with st.expander(f"DETAILED SOURCES ({chat['total_results']} results found)", expanded=False):
            for res in chat.get('document_results', [])[:3]:
                st.markdown(f"**{res.get('title', 'Unknown')}**")
                if res.get('author'):
                    st.markdown(f"*Author: {res['author']}*")
                if res.get('url'):
                    st.markdown(f"[View Source]({res['url']})")
                if res.get('snippet'):
                    st.info(res['snippet'])
                st.divider()
            for res in chat.get('web_results', [])[:2]:
                st.markdown(f"**{res.get('title', 'Unknown')}**")
                if res.get('url'):
                    st.markdown(f"[View Source]({res['url']})")
                if res.get('snippet'):
                    st.info(res['snippet'])
                st.divider()
        st.divider()
    
    # Add bottom padding for fixed input
    st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
    
    # Question input at bottom - Fixed position, only in dashboard
    st.markdown("""
    <div class="question-input-container">
        <textarea id="question-textarea" placeholder="Ask a question about Chinese exploration, Zheng He, or the 1421 theory..." rows="1"></textarea>
        <button id="research-btn" onclick="document.getElementById('research_btn').click();">Research</button>
    </div>
    """, unsafe_allow_html=True)
    
    # Hidden Streamlit components for the fixed input
    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_area(
            "Hidden question",
            value=st.session_state.current_question,
            key="dashboard_question",
            height=1,
            label_visibility="collapsed",
            placeholder=""
        )
    with col2:
        ask = st.button("RESEARCH", type="primary", key="research_btn", use_container_width=True)
    
    if (ask or st.session_state.auto_search) and question:
        st.session_state.auto_search = False
        with st.spinner("Researching historical records and searching the web..."):
            result = system.perform_search(question)
            
            # Add to current chat session
            for session in st.session_state.chat_sessions:
                if session['id'] == st.session_state.current_chat_id:
                    session['history'].append(result)
                    break
            
            # Auto-save to saved searches
            SavedSearchesSystem.save_search(
                question, result['answer'], result['sources_used'],
                result['document_results'], result['web_results']
            )
            st.rerun()

def show_documents_page(system):
    st.markdown('<h2 class="sub-header">RESEARCH DOCUMENTS</h2>', unsafe_allow_html=True)
    
    # Full width search input - no filter dropdown
    st.markdown('<div class="document-search-container">', unsafe_allow_html=True)
    search = st.text_input("", placeholder="Search documents by title, author, or keywords...", 
                          label_visibility="collapsed", key="doc_search")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Results per page selector
    col1, col2 = st.columns([1, 5])
    with col1:
        limit_opts = {"25": 25, "50": 50, "100": 100, "All": None}
        limit = limit_opts[st.selectbox("Show", ["All", "25", "50", "100"], index=0, label_visibility="collapsed")]
    
    c1, c2 = st.columns(2)
    search_btn = c1.button("SEARCH DOCUMENTS", type="primary", use_container_width=True)
    show_btn = c2.button("SHOW DOCUMENTS", use_container_width=True)
    
    docs = []
    if search_btn and search:
        docs = system.search_documents(search, limit or 1000)
        if docs:
            st.success(f"Found {len(docs)} documents")
    elif show_btn:
        docs = system.get_all_documents(limit)
        if docs:
            st.success(f"Loaded {len(docs)} documents")
    else:
        st.info("Enter a search query or click 'SHOW DOCUMENTS' to load all documents.")
    
    if docs:
        df = pd.DataFrame([{
            'ID': d.get('id', ''), 
            'Title': d.get('title', 'Untitled')[:50],
            'Author': d.get('author', 'Unknown')[:30], 
            'Type': d.get('source_type', 'Unknown'),
            'Words': d.get('word_count', 0),
            'URL': d.get('url', '')[:40] + '...' if len(d.get('url', '')) > 40 else d.get('url', '')
        } for d in docs])
        
        st.dataframe(df, column_config={
            "ID": "ID", "Title": "Document Title", "Author": "Author",
            "Type": "Type", "Words": "Words", "URL": st.column_config.LinkColumn("URL")
        }, use_container_width=True, height=500, hide_index=True)
        
        csv = df.to_csv(index=False).encode()
        st.download_button("DOWNLOAD AS CSV", csv, f"documents_{datetime.now():%Y%m%d}.csv", "text/csv", use_container_width=True)

def show_map_page(system):
    st.markdown('<h2 class="sub-header">FULL VOYAGE MAP</h2>', unsafe_allow_html=True)
    
    with st.spinner("Loading geographical data..."):
        try:
            map_data = system.get_map_locations()
            st.session_state.map_data = map_data
            
            if map_data and map_data['locations']:
                locations = map_data['locations']
                timeline_events = map_data.get('timeline_events', [])
                
                # Animation controls
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    current_year = st.session_state.current_year
                    year = st.slider("Year", 1368, 1421, current_year, key="map_year_slider")
                    st.session_state.current_year = year
                
                with col2:
                    if st.button("Play", key="play_animation", use_container_width=True):
                        st.session_state.animation_playing = True
                
                with col3:
                    if st.button("Pause", key="pause_animation", use_container_width=True):
                        st.session_state.animation_playing = False
                
                with col4:
                    if st.button("Reset", key="reset_animation", use_container_width=True):
                        st.session_state.current_year = 1368
                        st.session_state.animation_playing = False
                        st.rerun()
                
                # Animation logic
                if st.session_state.animation_playing:
                    if st.session_state.current_year < 1421:
                        st.session_state.current_year += 1
                        time.sleep(1)  # 1 second per year
                        st.rerun()
                    else:
                        st.session_state.animation_playing = False
                
                # Filter locations by current year
                filtered_locs = [loc for loc in locations if loc.get('year', 1400) <= st.session_state.current_year]
                
                # Create map without title
                fig = go.Figure()
                
                if filtered_locs:
                    lats = [loc['lat'] for loc in filtered_locs]
                    lons = [loc['lon'] for loc in filtered_locs]
                    names = [loc['name'] for loc in filtered_locs]
                    years = [loc.get('year', 1400) for loc in filtered_locs]
                    events = [loc.get('event', 'Historical location') for loc in filtered_locs]
                    
                    fig.add_trace(go.Scattergeo(
                        lon=lons, lat=lats,
                        mode='markers+text',
                        marker=dict(
                            size=12,
                            color=years,
                            colorscale='Viridis',
                            colorbar=dict(title="Year", x=1.02),
                            line=dict(width=1, color='white'),
                            symbol='circle'
                        ),
                        text=names,
                        textposition="top center",
                        name='Historical Locations',
                        hovertemplate='<b>%{text}</b><br>Year: %{marker.color}<br>Event: %{customdata}<extra></extra>',
                        customdata=events
                    ))
                    
                    # Add voyage routes
                    if len(filtered_locs) > 2:
                        sorted_locs = sorted(filtered_locs, key=lambda x: x.get('year', 1400))
                        route_lats = [loc['lat'] for loc in sorted_locs]
                        route_lons = [loc['lon'] for loc in sorted_locs]
                        
                        fig.add_trace(go.Scattergeo(
                            lon=route_lons, lat=route_lats,
                            mode='lines',
                            line=dict(width=2, color='#d4af37', dash='dash'),
                            name='Voyage Route',
                            hoverinfo='none'
                        ))
                
                fig.update_layout(
                    title=None,
                    geo=dict(
                        showland=True,
                        landcolor='rgb(243,243,243)',
                        coastlinecolor='rgb(204,204,204)',
                        showcountries=True,
                        countrycolor='rgb(204,204,204)',
                        showocean=True,
                        oceancolor='rgb(230,245,255)',
                        projection_type='natural earth',
                        showlakes=True,
                        lakecolor='rgb(230,245,255)'
                    ),
                    height=600,
                    showlegend=True,
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Timeline
                st.divider()
                st.subheader("Historical Timeline")
                
                if timeline_events:
                    timeline_df = pd.DataFrame(timeline_events)
                    timeline_df = timeline_df[timeline_df['year'] <= st.session_state.current_year]
                    timeline_df = timeline_df.sort_values('year')
                    
                    fig_timeline = go.Figure()
                    
                    for i, event in enumerate(timeline_events):
                        if event['year'] <= st.session_state.current_year:
                            fig_timeline.add_trace(go.Scatter(
                                x=[event['year'], event['year']],
                                y=[i, i+0.8],
                                mode='lines',
                                line=dict(width=10, color='#d4af37'),
                                name=event['location'],
                                hoverinfo='text',
                                text=f"<b>{event['location']}</b><br>Year: {event['year']}<br>{event['event']}",
                                showlegend=False
                            ))
                    
                    fig_timeline.add_trace(go.Scatter(
                        x=timeline_df['year'],
                        y=[0.5] * len(timeline_df),
                        mode='markers+text',
                        marker=dict(size=8, color='#4a6491'),
                        text=timeline_df['location'],
                        textposition='top center',
                        hoverinfo='text',
                        hovertemplate='<b>%{text}</b><br>Year: %{x}<extra></extra>',
                        name='Locations',
                        showlegend=False
                    ))
                    
                    fig_timeline.update_layout(
                        title=f"Exploration Timeline (1368-{st.session_state.current_year})",
                        xaxis_title="Year",
                        xaxis=dict(range=[1368, 1421]),
                        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[0, len(timeline_events)+1]),
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    
                    st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    with st.expander("Timeline Details", expanded=True):
                        for year in sorted(timeline_df['year'].unique()):
                            year_events = timeline_df[timeline_df['year'] == year]
                            st.markdown(f"### {year}")
                            for _, event in year_events.iterrows():
                                st.markdown(f"**{event['location']}**: {event['event']}")
                            st.divider()
                else:
                    st.info("No timeline data available.")
            else:
                st.info("No geographical location data available.")
        except Exception as e:
            st.error(f"Error loading map data: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

def show_analytics_page(system):
    st.markdown('<h2 class="sub-header">ANALYTICS DASHBOARD</h2>', unsafe_allow_html=True)
    
    a = st.session_state.search_analytics
    stats = system.get_database_stats()
    
    if stats:
        cols = st.columns(4)
        cols[0].metric("Total Searches", a['total_searches'])
        cols[1].metric("Avg Response Time", f"{sum(a['response_times'])/max(1,len(a['response_times'])):.2f}s")
        cols[2].metric("Active Days", len(a['searches_by_day']))
        cols[3].metric("Saved Searches", stats.get('saved_searches', 0))
        
        if a['sources_used']:
            st.subheader("Source Usage")
            c1, c2, c3 = st.columns(3)
            c1.metric("Document Searches", a['sources_used']['documents'])
            c2.metric("Web Searches", a['sources_used']['web'])
            c3.metric("Combined Searches", a['sources_used']['both'])
        
        if a['popular_topics']:
            st.subheader("Top Search Topics")
            topics_df = pd.DataFrame(list(a['popular_topics'].items()), columns=['Topic', 'Count'])
            topics_df = topics_df.sort_values('Count', ascending=False).head(10)
            fig = px.bar(topics_df, x='Count', y='Topic', orientation='h', color='Count', color_continuous_scale='Oranges')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No analytics data available yet. Start searching to generate analytics.")

def show_settings_page(system):
    st.markdown('<h2 class="sub-header">SYSTEM SETTINGS</h2>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Database Information")
        stats = system.get_database_stats()
        if stats:
            st.write(f"**Total Documents:** {stats['total_documents']}")
            st.write(f"**Saved Searches:** {stats['saved_searches']}")
            st.write(f"**Geocoded Locations:** {stats['geocoded_locations']}")
    
    with c2:
        st.subheader("System Status")
        st.write(f"**Database Path:** `{system.db_path}`")
        st.write(f"**Database Connection:** {'Active' if system.db else 'Inactive'}")
        st.write(f"**Web Search Module:** {'Active' if system.web_searcher else 'Inactive'}")
        
        openai_status = 'Inactive (API key not set)'
        if hasattr(system.web_searcher, 'openai_client'):
            openai_status = 'Active' if system.web_searcher.openai_client else 'Inactive (API key not set)'
        st.write(f"**OpenAI Integration:** {openai_status}")
    
    st.divider()
    st.subheader("Search Mode")
    
    # LLM Thinking Mode selector
    mode = st.radio(
        "Select how the system should search for information:",
        options=["Auto (Documents + Web)", "Documents Only", "Web Only"],
        index=0,
        horizontal=True,
        help="Auto mode uses documents first, then falls back to web. Documents Only uses only the local database. Web Only uses only internet search."
    )
    st.session_state.search_mode = mode
    
    st.divider()
    st.subheader("Actions")
    
    c1, c2 = st.columns(2)
    if c1.button("REFRESH CACHE", use_container_width=True):
        st.cache_resource.clear()
        st.success("System cache cleared!")
        st.rerun()
    
    if c2.button("CHECK DATABASE", use_container_width=True):
        if system.db:
            try:
                cursor = system.db.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                st.success(f"Database connection OK. Found {len(tables)} tables.")
            except Exception as e:
                st.error(f"Database error: {str(e)}")
        else:
            st.error("Database not initialized")
    
    st.divider()
    st.subheader("Data Management")
    
    if st.button("CLEAR CHAT HISTORY", use_container_width=True):
        st.session_state.chat_sessions = [{
            'id': 0,
            'name': 'New Chat',
            'history': [],
            'created': datetime.now().strftime("%Y-%m-%d %H:%M")
        }]
        st.session_state.current_chat_id = 0
        st.success("Chat history cleared!")
        st.rerun()
    
    if st.button("CLEAR ALL SAVED SEARCHES", use_container_width=True):
        st.session_state.saved_searches = []
        st.success("All saved searches cleared!")
        st.rerun()
    
    if st.button("RESET ANALYTICS DATA", use_container_width=True):
        st.session_state.search_analytics = DEFAULT_ANALYTICS.copy()
        st.success("Analytics data reset!")
        st.rerun()

# ========== SIDEBAR ==========
def render_sidebar():
    with st.sidebar:
        st.markdown('<div style="text-align: center; margin-bottom: 0.8rem;"><h2 style="color: #d4af37; font-size: 1.8rem; margin-bottom: 0;">1421 AI</h2><p style="color: #fff; opacity: 0.8; margin-top: 0; font-size: 0.8rem;">HISTORICAL RESEARCH SYSTEM</p></div>', unsafe_allow_html=True)
        
        # Navigation - all buttons close together with larger text
        pages = [
            ("DASHBOARD", "dashboard"),
            ("RESEARCH DOCUMENTS", "documents"),
            ("FULL VOYAGE MAP", "map"),
            ("ANALYTICS", "analytics"),
            ("SEND FEEDBACK", "feedback"),
            ("SETTINGS", "settings")
        ]
        
        for label, pid in pages:
            btn_type = "primary" if st.session_state.current_page == pid else "secondary"
            if st.button(label, key=f"nav_{pid}", use_container_width=True, type=btn_type):
                st.session_state.current_page = pid
                st.rerun()
        
        # System status (minimal)
        if 'system_stats' in st.session_state:
            stats = st.session_state.system_stats
            st.sidebar.markdown("---")
            st.sidebar.markdown('<h3 style="color: #FFD700; font-size: 0.9rem; margin-bottom: 5px;">SYSTEM</h3>', unsafe_allow_html=True)
            st.sidebar.markdown(f'<p style="color: white; margin: 2px 0; font-size: 0.8rem;">📄 {stats.get("total_documents",0)} docs</p>', unsafe_allow_html=True)
            st.sidebar.markdown(f'<p style="color: white; margin: 2px 0; font-size: 0.8rem;">💾 {stats.get("saved_searches",0)} saved</p>', unsafe_allow_html=True)

# ========== MAIN ==========
def main():
    st.markdown('''
    <div style="text-align: center; padding: 0.5rem 0 0.5rem 0;">
        <h1 class="main-header">1421 AI - HISTORICAL RESEARCH SYSTEM</h1>
    </div>
    ''', unsafe_allow_html=True)
    
    system = init_system()
    if not system or not system.db:
        st.error("""
        ## SYSTEM INITIALIZATION FAILED
        
        **Troubleshooting Steps:**
        1. Make sure `knowledge_base.db` is in the `data/` folder
        2. Check the file is properly uploaded to GitHub
        3. Verify database is not corrupted
        """)
        st.stop()
    
    st.session_state.system_stats = system.get_database_stats()
    render_sidebar()
    
    # Main content area with right sidebar for chat/saved searches
    if st.session_state.current_page == "dashboard":
        # Two-column layout for dashboard only
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Dashboard content
            show_dashboard(system)
        
        with col2:
            # Right sidebar with chat sessions and saved searches
            SavedSearchesSystem.render_chat_sidebar()
    else:
        # Other pages - full width
        if st.session_state.current_page == "feedback":
            FeedbackSystem.render_feedback_page()
        elif st.session_state.current_page == "documents":
            show_documents_page(system)
        elif st.session_state.current_page == "map":
            show_map_page(system)
        elif st.session_state.current_page == "analytics":
            show_analytics_page(system)
        elif st.session_state.current_page == "settings":
            show_settings_page(system)

@st.cache_resource
def init_system():
    return ResearchSystem()

if __name__ == "__main__":
    main()
