"""1421 Foundation AI - Historical Research System
Professional version with analytics, saved searches, and feedback
FIXED: DeepSeek-style streaming responses
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
    page_title="1421 Foundation AI - Historical Research System",
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
    'deleting_search_id': None,
    'feedback_submitted': False,
    'animation_playing': False,
    'current_year': 1368,
    'map_data': None,
    'search_mode': 'Auto (Documents + Web)',
    'chat_sessions': [],
    'current_chat_id': 0,
    'map_fullscreen': False,
    'show_world_map': True
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Initialize default chat session
if not st.session_state.chat_sessions:
    st.session_state.chat_sessions = [{
        'id': 0,
        'name': 'Chat 1',
        'history': [],
        'created': datetime.now().strftime("%Y-%m-%d %H:%M")
    }]

# ========== CSS STYLING - Professional, No Emojis ==========
st.markdown("""
<style>
/* Main styling */
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
.main .block-container { 
    background: rgba(255,255,255,0.98); 
    border-radius: 15px; 
    padding: 1.5rem 2rem; 
    margin-top: 1rem; 
    box-shadow: 0 6px 20px rgba(0,0,0,0.1); 
    max-width: 1400px; 
    margin-left: auto; 
    margin-right: auto; 
    min-height: calc(100vh - 100px);
    position: relative;
    padding-bottom: 100px;
}

/* Remove extra spacing */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
}

/* Headers - No emojis */
.main-header { 
    font-size: 2.2rem; 
    color: #000; 
    text-align: center; 
    margin-bottom: 0.3rem; 
    font-weight: 800; 
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%); 
    -webkit-background-clip: text; 
    -webkit-text-fill-color: transparent; 
}
.sub-header { 
    font-size: 1.6rem; 
    color: #2c3e50; 
    margin-bottom: 1rem; 
    font-weight: 700; 
    border-bottom: 3px solid #d4af37; 
    padding-bottom: 0.3rem; 
}

/* Left Navigation Sidebar */
section[data-testid="stSidebar"] > div { 
    background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%) !important; 
    border-right: 4px solid #d4af37;
    padding-top: 1rem !important;
    width: 100%;
}

/* Navigation buttons - Yellow background with black text */
.stSidebar .stButton > button {
    background: #d4af37 !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 6px;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 6px 10px !important;
    margin: 1px 0 !important;
    text-align: left;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.2s ease;
    width: 100%;
    border-bottom: 2px solid transparent !important;
}

.stSidebar .stButton > button:hover {
    background: #c4a030 !important;
    transform: translateX(3px);
    border-bottom: 2px solid #000000 !important;
}

.stSidebar .stButton > button[kind="primary"] {
    background: #d4af37 !important;
    color: #000000 !important;
    font-weight: 700 !important;
    border: 2px solid #ffffff !important;
}

/* Chat History in Left Sidebar - ABOVE System Status */
.chat-history-section {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 2px solid rgba(212,175,55,0.3);
}

.chat-history-header {
    color: #d4af37;
    font-size: 0.85rem;
    font-weight: 700;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* System Status - Clean, no background */
.system-status-container {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 2px solid rgba(212,175,55,0.3);
}

.system-status-container p {
    color: #d4af37;
    margin: 3px 0;
    font-size: 0.75rem;
}

.system-status-container span {
    color: white;
}

/* Metrics - Black text for labels */
[data-testid="stMetricValue"] { 
    font-size: 1.8rem !important; 
    font-weight: 700 !important; 
    color: #2c3e50 !important; 
}
[data-testid="stMetricLabel"] { 
    font-weight: 600 !important; 
    font-size: 0.9rem !important; 
    color: #000000 !important; 
}

/* Answer display - NO MORE typing animation needed */
.answer-text { 
    font-size: 1rem; 
    line-height: 1.5; 
    color: #2c3e50; 
    margin: 5px 0; 
    padding: 0; 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}

/* Chat message styling - REDUCED SPACING */
.chat-message { 
    padding: 8px 12px; 
    margin: 5px 0; 
    border-radius: 12px; 
    max-width: 80%; 
    animation: fadeIn 0.3s ease; 
}
.user-message { 
    background: #f0f0f0; 
    color: #333; 
    margin-left: auto; 
    margin-right: 0; 
    border-radius: 18px 18px 4px 18px; 
}
.assistant-message { 
    background: white; 
    color: #333; 
    margin-right: auto; 
    margin-left: 0; 
    border-radius: 18px 18px 18px 4px; 
    border: 1px solid #eaeaea; 
}

/* Remove extra spacing between messages */
div[data-testid="stVerticalBlock"] > div {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

.stMarkdown {
    margin-bottom: 0 !important;
}

hr {
    margin: 10px 0 !important;
}

/* Action buttons - Copy only */
.action-buttons { 
    display: flex; 
    gap: 10px; 
    margin-top: 5px; 
    margin-bottom: 5px; 
}

/* Chat container - REDUCED SPACING */
.chat-container {
    margin-bottom: 80px;
    min-height: 400px;
    padding: 0;
}

/* Document buttons */
.doc-button, .stButton > button {
    background: #d4af37 !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 6px;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 6px 16px !important;
    transition: all 0.3s ease !important;
}

.doc-button:hover, .stButton > button:hover {
    background: #c4a030 !important;
    transform: translateY(-2px);
}

/* How to use section - REDUCED SPACING */
.how-to-use {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 12px;
    padding: 15px 20px;
    margin: 10px 0;
    border-left: 6px solid #d4af37;
}

.how-to-use h3 {
    color: #2c3e50;
    margin-bottom: 10px;
    font-weight: 700;
    font-size: 1.2rem;
}

.how-to-use p {
    color: #333;
    margin-bottom: 8px;
    line-height: 1.5;
    font-size: 0.95rem;
}

.how-to-use li {
    color: #333;
    margin-bottom: 5px;
    font-size: 0.95rem;
}

/* Coming soon badge */
.coming-soon {
    background: #f0f0f0;
    color: #666;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    font-style: italic;
    border: 1px dashed #999;
    font-size: 0.95rem;
}

/* Scrollable chat history */
.chat-history-scroll {
    max-height: 200px;
    overflow-y: auto;
    padding-right: 3px;
}

.chat-history-scroll::-webkit-scrollbar {
    width: 4px;
}

.chat-history-scroll::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
}

.chat-history-scroll::-webkit-scrollbar-thumb {
    background: #d4af37;
    border-radius: 10px;
}
</style>
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
            <h3 style="color: #2c3e50; margin-bottom: 20px;">Help us improve 1421 Foundation AI</h3>
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
        
        col1, col2 = st.columns([1, 1])
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
            {'name': 'Calicut', 'lat': 11.2588, 'lon': 75.7804, 'year': 1406, 'event': 'Zheng He fleet first arrived'},
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
    
    def _stream_text(self, text, placeholder):
        """Stream text word by word to placeholder - DeepSeek style"""
        words = text.split()
        displayed = ""
        for i, word in enumerate(words):
            displayed += word + " "
            # Show cursor while typing
            placeholder.markdown(displayed + "▌")
            time.sleep(0.04)  # Adjust speed (lower = faster, 0.04 = 25 words/sec)
        # Remove cursor when done
        placeholder.markdown(displayed.strip())
    
    def generate_intelligent_answer_stream(self, question, doc_results, web_results, mode, placeholder):
        """Generate streaming answer word-by-word like DeepSeek"""
        sources = []
        
        if not doc_results and not web_results:
            full_text = "I could not find specific information about that in our historical database or on the web. Please try rephrasing your question or using different keywords."
            self._stream_text(full_text, placeholder)
            return full_text, []
        
        # Determine which sources to use based on mode
        use_docs = mode in ['Auto (Documents + Web)', 'Documents Only']
        use_web = mode in ['Auto (Documents + Web)', 'Web Only']
        
        if use_docs and doc_results:
            sources.append('documents')
        if use_web and web_results:
            sources.append('web')
        
        # If no sources after filtering, fallback
        if not sources:
            full_text = "No information available with current search settings. Please try changing your search mode."
            self._stream_text(full_text, placeholder)
            return full_text, []
        
        # Try OpenAI streaming first
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
                
                # Stream the response word-by-word
                stream = self.web_searcher.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional historian specialising in early Chinese maritime exploration. You write in clear, academic UK English and synthesise information rather than copying it."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=700,
                    temperature=0.7,
                    stream=True
                )
                
                full_answer = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_answer += content
                        # Show with cursor
                        placeholder.markdown(full_answer + "▌")
                        time.sleep(0.02)  # Control streaming speed
                
                # Remove cursor when done
                placeholder.markdown(full_answer)
                # Remove any URLs just in case
                full_answer = re.sub(r'https?://\S+', '', full_answer)
                return full_answer, sources
                
            except Exception as e:
                print(f"OpenAI streaming failed: {e}")
        
        # Enhanced fallback with better synthesis
        key_points = []
        
        if use_docs and doc_results:
            for d in doc_results[:3]:
                content = d.get('snippet', d.get('content', ''))[:200]
                # Clean and summarise
                content = re.sub(r'#\S+', '', content)
                content = re.sub(r'https?://\S+', '', content)
                content = ' '.join(content.split())
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
        
        full_text = ''.join(response_parts)
        self._stream_text(full_text, placeholder)
        return full_text, sources
    
    def perform_search(self, question, answer_placeholder=None):
        start = time.time()
        mode = st.session_state.get('search_mode', 'Auto (Documents + Web)')
        
        # Search based on mode
        docs = []
        web = []
        
        if mode in ['Auto (Documents + Web)', 'Documents Only']:
            docs = self.search_documents(question, 10)
        
        if mode in ['Auto (Documents + Web)', 'Web Only']:
            if mode == 'Web Only' or (mode == 'Auto (Documents + Web)' and not docs):
                time.sleep(0.3)
                web = self.web_searcher.search_google(question, 3)
        
        # Generate streaming answer
        if answer_placeholder:
            answer, sources = self.generate_intelligent_answer_stream(question, docs, web, mode, answer_placeholder)
        else:
            # Fallback if no placeholder provided (shouldn't happen)
            answer = "Error: No answer placeholder provided"
            sources = []
        
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

# ========== LEFT SIDEBAR ==========
def render_left_sidebar():
    with st.sidebar:
        st.markdown('<div style="text-align: center; margin-bottom: 0.5rem;"><h2 style="color: #d4af37; font-size: 1.4rem; margin-bottom: 0;">1421 FOUNDATION AI</h2><p style="color: #fff; opacity: 0.8; margin-top: 0; font-size: 0.65rem;">HISTORICAL RESEARCH SYSTEM</p></div>', unsafe_allow_html=True)
        
        # Navigation - Yellow background with black text
        pages = [
            ("DASHBOARD", "dashboard"),
            ("CHAT", "chat"),
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
        
        # CHAT HISTORY - ABOVE System Status
        st.sidebar.markdown('<div class="chat-history-section">', unsafe_allow_html=True)
        st.sidebar.markdown('<div class="chat-history-header">CHAT HISTORY</div>', unsafe_allow_html=True)
        
        # New Chat button
        if st.sidebar.button("+ NEW CHAT", key="new_chat_btn_sidebar", use_container_width=True):
            new_id = len(st.session_state.chat_sessions)
            st.session_state.chat_sessions.append({
                'id': new_id,
                'name': f'Chat {new_id + 1}',
                'history': [],
                'created': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.session_state.current_chat_id = new_id
            st.rerun()
        
        # Chat sessions - scrollable
        st.sidebar.markdown('<div class="chat-history-scroll">', unsafe_allow_html=True)
        for session in st.session_state.chat_sessions[-10:][::-1]:
            chat_key = f"chat_select_sidebar_{session['id']}"
            if st.sidebar.button(f"{session['name']}", key=chat_key, use_container_width=True):
                st.session_state.current_chat_id = session['id']
                st.rerun()
        
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
        
        # System Status in left sidebar (BELOW Chat History)
        if 'system_stats' in st.session_state:
            stats = st.session_state.system_stats
            st.sidebar.markdown('<div class="system-status-container">', unsafe_allow_html=True)
            st.sidebar.markdown('<div class="chat-history-header">SYSTEM STATUS</div>', unsafe_allow_html=True)
            st.sidebar.markdown(f'''
                <p style="color: #d4af37; margin: 3px 0;"><strong>Documents:</strong> <span style="color: white;">{stats.get("total_documents",0)}</span></p>
                <p style="color: #d4af37; margin: 3px 0;"><strong>Chats:</strong> <span style="color: white;">{len(st.session_state.chat_sessions)}</span></p>
                <p style="color: #d4af37; margin: 3px 0;"><strong>Locations:</strong> <span style="color: white;">{stats.get("geocoded_locations",25)}</span></p>
            ''', unsafe_allow_html=True)
            st.sidebar.markdown('</div>', unsafe_allow_html=True)

# ========== PAGE FUNCTIONS ==========
def show_dashboard(system):
    st.markdown('<h2 class="sub-header">DASHBOARD</h2>', unsafe_allow_html=True)
    
    stats = system.get_database_stats()
    if stats:
        cols = st.columns(4)
        cols[0].metric("Total Documents", stats['total_documents'])
        cols[1].metric("Saved Searches", stats['saved_searches'])
        cols[2].metric("Geocoded Locations", stats['geocoded_locations'])
        cols[3].metric("Database Status", "Active" if system.db else "Inactive")
    
    st.divider()
    
    # How to Use This System Section
    st.markdown("""
    <div class="how-to-use">
        <h3>HOW TO USE 1421 FOUNDATION AI</h3>
        <p>Welcome to the 1421 Foundation AI Historical Research System. This platform helps you explore Chinese maritime history, Zheng He's voyages, and the 1421 theory through both historical documents and web research.</p>
        <ul>
            <li><strong>CHAT:</strong> Use the Chat section to ask questions. Each chat session is saved automatically in the left sidebar.</li>
            <li><strong>RESEARCH DOCUMENTS:</strong> Browse and search through our historical document database.</li>
            <li><strong>VOYAGE MAP:</strong> Visualise voyage routes and explore locations on the interactive world map with fullscreen support.</li>
            <li><strong>ANALYTICS:</strong> View search statistics and popular topics.</li>
        </ul>
        <p style="margin-top: 10px; color: #d4af37; font-weight: 600;">Click on any example question below to start a new chat:</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h3 style="color: #2c3e50; margin-top: 10px; font-size: 1.2rem;">EXAMPLE QUESTIONS</h3>', unsafe_allow_html=True)
    
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
                # Create a new chat session
                new_id = len(st.session_state.chat_sessions)
                st.session_state.chat_sessions.append({
                    'id': new_id,
                    'name': f'Chat {new_id + 1}',
                    'history': [],
                    'created': datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.session_state.current_chat_id = new_id
                st.session_state.current_question = q
                st.session_state.auto_search = True
                st.session_state.current_page = "chat"
                st.rerun()

def show_chat_page(system):
    """Dedicated Chat page with DeepSeek-style streaming"""
    
    # Get current chat history
    current_chat_id = st.session_state.current_chat_id
    current_session = next((s for s in st.session_state.chat_sessions if s['id'] == current_chat_id), None)
    
    if current_session:
        chat_history = current_session['history']
        chat_name = current_session['name']
    else:
        chat_history = []
        chat_name = "New Chat"
    
    st.markdown(f'<h2 class="sub-header">CHAT: {chat_name}</h2>', unsafe_allow_html=True)
    
    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Chat history for current session
    if chat_history:
        for idx, chat in enumerate(chat_history):
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong><br>{chat["question"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-message assistant-message"><strong>1421 Foundation AI:</strong><br><div class="answer-text">{chat["answer"]}</div></div>', unsafe_allow_html=True)
            st.markdown('<hr style="margin: 8px 0;">', unsafe_allow_html=True)
    else:
        # Welcome message
        st.markdown("""
        <div style="text-align: center; padding: 30px 20px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; margin: 10px 0;">
            <h3 style="color: #2c3e50; margin-bottom: 10px;">Welcome to 1421 Foundation AI Chat</h3>
            <p style="color: #666; font-size: 1rem;">Ask any question about Chinese exploration, Zheng He's voyages, or the 1421 theory.</p>
            <p style="color: #d4af37; margin-top: 10px;">Type your question below to begin...</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area
    question = st.text_area(
        "Your Question",
        value=st.session_state.current_question,
        key="chat_question",
        height=80,
        placeholder="Message 1421 Foundation AI..."
    )
    
    col1, col2 = st.columns([4, 1])
    with col2:
        ask = st.button("SEARCH", type="primary", key="chat_research_btn", use_container_width=True)
    
    if (ask or st.session_state.auto_search) and question:
        st.session_state.auto_search = False
        
        # Show user message immediately
        st.markdown(f'<div class="chat-message user-message"><strong>You:</strong><br>{question}</div>', unsafe_allow_html=True)
        
        # Create placeholder for streaming answer
        assistant_container = st.empty()
        assistant_container.markdown('<div class="chat-message assistant-message"><strong>1421 Foundation AI:</strong><br><div class="answer-text">Searching...</div></div>', unsafe_allow_html=True)
        
        # Create placeholder for the actual streaming text
        answer_placeholder = st.empty()
        
        # Perform search with streaming
        with st.spinner("Researching historical records and searching the web..."):
            result = system.perform_search(question, answer_placeholder)
            
            # Add to current chat session
            for session in st.session_state.chat_sessions:
                if session['id'] == st.session_state.current_chat_id:
                    session['history'].append(result)
                    if len(session['history']) == 1:
                        session['name'] = question[:20] + ('...' if len(question) > 20 else '')
                    break
            
            st.session_state.current_question = ""
            time.sleep(0.5)
            st.rerun()

def show_documents_page(system):
    st.markdown('<h2 class="sub-header">RESEARCH DOCUMENTS</h2>', unsafe_allow_html=True)
    
    # Document controls - search and limit on same line
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search = st.text_input("", placeholder="Search documents by title, author, or keywords...", 
                              label_visibility="collapsed", key="doc_search")
    
    with col2:
        limit_opts = {"25": 25, "50": 50, "100": 100, "All": None}
        limit = limit_opts[st.selectbox("Show", ["All", "25", "50", "100"], index=0, label_visibility="collapsed")]
    
    # Action buttons
    c1, c2 = st.columns(2)
    with c1:
        search_btn = st.button("SEARCH DOCUMENTS", key="search_docs_btn", use_container_width=True)
    with c2:
        show_btn = st.button("SHOW DOCUMENTS", key="show_docs_btn", use_container_width=True)
    
    docs = []
    if search_btn and search:
        docs = system.search_documents(search, limit or 1000)
        if docs:
            st.success(f"Found {len(docs)} documents matching '{search}'")
    elif show_btn:
        docs = system.get_all_documents(limit)
        if docs:
            st.success(f"Loaded {len(docs)} documents")
    else:
        st.info("Enter a search query or click 'SHOW DOCUMENTS' to load all documents from the database.")
    
    if docs:
        df = pd.DataFrame([{
            'ID': d.get('id', ''), 
            'Title': d.get('title', 'Untitled')[:50],
            'Author': d.get('author', 'Unknown')[:25], 
            'Type': d.get('source_type', 'Unknown'),
            'Words': d.get('word_count', 0),
            'URL': d.get('url', '')[:35] + '...' if len(d.get('url', '')) > 35 else d.get('url', '')
        } for d in docs])
        
        st.dataframe(df, use_container_width=True, height=450, hide_index=True)

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
    else:
        st.info("No analytics data available yet. Start searching to generate analytics.")

def show_settings_page(system):
    st.markdown('<h2 class="sub-header">SYSTEM SETTINGS</h2>', unsafe_allow_html=True)
    st.info("Settings page coming soon...")

def show_map_page(system):
    st.markdown('<h2 class="sub-header">FULL VOYAGE MAP</h2>', unsafe_allow_html=True)
    st.info("Interactive voyage map coming soon...")

# ========== MAIN ==========
def main():
    st.markdown('''
    <div style="text-align: center; padding: 0.3rem 0 0.3rem 0;">
        <h1 class="main-header">1421 FOUNDATION AI - HISTORICAL RESEARCH SYSTEM</h1>
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
    
    # Render left sidebar
    render_left_sidebar()
    
    # Main content area
    if st.session_state.current_page == "dashboard":
        show_dashboard(system)
    elif st.session_state.current_page == "chat":
        show_chat_page(system)
    elif st.session_state.current_page == "documents":
        show_documents_page(system)
    elif st.session_state.current_page == "map":
        show_map_page(system)
    elif st.session_state.current_page == "analytics":
        show_analytics_page(system)
    elif st.session_state.current_page == "settings":
        show_settings_page(system)
    elif st.session_state.current_page == "feedback":
        FeedbackSystem.render_feedback_page()

@st.cache_resource
def init_system():
    return ResearchSystem()

if __name__ == "__main__":
    main()
