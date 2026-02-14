"""
1421 Foundation AI Research System
Complete Streamlit Application - Single File
Uses GPT-4o-mini, SQLite, and vector database support
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
import hashlib

# Optional imports - graceful fallback
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from googlesearch import search as google_search
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="1421 Foundation AI Research System",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"  # Changed from "collapsed" to "expanded"
)

# ========== INITIALIZE SESSION STATE ==========
DEFAULT_ANALYTICS = {
    'total_searches': 0, 'searches_by_day': {}, 'searches_by_hour': {},
    'questions_asked': [], 'response_times': [], 'popular_topics': {},
    'user_sessions': [], 'sources_used': {'documents': 0, 'web': 0, 'both': 0}
}

DEFAULT_STATE = {
    'search_analytics': DEFAULT_ANALYTICS,
    'current_page': 'dashboard',
    'current_question': '',
    'auto_search': False,
    'feedback_submitted': False,
    'animation_playing': False,
    'current_year': 1368,
    'map_data': None,
    'search_mode': 'Auto (Documents + Web)',
    'chat_sessions': [],
    'current_chat_id': 0,
    'show_nav': True,
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
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

/* Main styling */
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
.main .block-container {
    background: rgba(255,255,255,0.98);
    border-radius: 15px;
    padding: 2rem;
    margin-top: 1rem;
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    max-width: 1400px;
    margin-left: auto;
    margin-right: auto;
}

/* Brand font */
.brand-title {
    font-family: 'Cinzel', serif !important;
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.3rem;
    letter-spacing: 1px;
}

.brand-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: #888;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
}

/* Headers */
.sub-header {
    font-family: 'Cinzel', serif !important;
    font-size: 1.6rem;
    color: #2c3e50;
    margin-bottom: 1.5rem;
    font-weight: 700;
    border-bottom: 3px solid #d4af37;
    padding-bottom: 0.5rem;
}

/* Sidebar styling */
section[data-testid="stSidebar"] > div {
    background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%) !important;
    border-right: 4px solid #d4af37;
    padding-top: 1rem !important;
}

/* Nav buttons */
.stSidebar .stButton > button {
    background: #d4af37 !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 6px;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 10px 14px !important;
    margin: 2px 0 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.2s ease;
    width: 100%;
    text-align: left;
}

.stSidebar .stButton > button:hover {
    background: #c4a030 !important;
    transform: translateX(3px);
}

.stSidebar .stButton > button[kind="primary"] {
    background: #d4af37 !important;
    color: #000000 !important;
    font-weight: 700 !important;
    border: 2px solid #ffffff !important;
}

/* Chat history sidebar items */
.chat-history-header {
    color: #d4af37;
    font-family: 'Cinzel', serif;
    font-size: 0.95rem;
    font-weight: 700;
    margin: 15px 0 10px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Metrics */
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: #2c3e50 !important;
}
[data-testid="stMetricLabel"] {
    font-weight: 600 !important;
    font-size: 1rem !important;
    color: #d4af37 !important;
}

/* Chat messages */
.chat-message {
    padding: 18px;
    margin: 12px 0;
    border-radius: 12px;
    max-width: 100%;
    animation: fadeIn 0.3s ease;
}
.user-message {
    background: linear-gradient(135deg, #4a6491 0%, #2c3e50 100%);
    color: white;
    margin-right: 15%;
    border-bottom-right-radius: 4px;
}
.assistant-message {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    color: #333;
    border: 1px solid #ddd;
    margin-left: 15%;
    border-bottom-left-radius: 4px;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Source badges */
.source-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 6px;
}
.badge-document { background: #4a6491; color: white; }
.badge-web { background: #28a745; color: white; }

/* How to use */
.how-to-use {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 12px;
    padding: 25px;
    margin: 20px 0;
    border-left: 6px solid #d4af37;
}

/* Chat input fixed at bottom */
.chat-input-area {
    position: sticky;
    bottom: 0;
    background: white;
    padding: 15px 0;
    border-top: 1px solid #eee;
    z-index: 100;
}

/* Main content buttons */
.stButton > button {
    background: #d4af37 !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 6px;
    font-weight: 600 !important;
}
.stButton > button:hover {
    background: #c4a030 !important;
}

/* Fullscreen map button */
.fullscreen-map-btn {
    background: #d4af37;
    color: #000;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    cursor: pointer;
}

/* Timeline styling - ADDED */
.timeline-container {
    margin-top: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 12px;
}

.timeline-year {
    font-family: 'Cinzel', serif;
    color: #d4af37;
    font-weight: 700;
    font-size: 1.2rem;
    margin-bottom: 10px;
}

.timeline-event {
    padding: 8px 0;
    border-bottom: 1px solid #ddd;
}

/* Example question buttons */
.example-question-btn {
    background: #f8f9fa;
    border: 1px solid #d4af37;
    border-radius: 6px;
    padding: 8px;
    margin: 4px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
}

.example-question-btn:hover {
    background: #d4af37;
    color: #000;
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
        if HAS_OPENAI:
            try:
                api_key = None
                if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                    api_key = st.secrets['OPENAI_API_KEY']
                elif 'OPENAI_API_KEY' in os.environ:
                    api_key = os.environ['OPENAI_API_KEY']
                if api_key:
                    self.openai_client = openai.OpenAI(api_key=api_key)
            except Exception:
                self.openai_client = None

    def search_google(self, query: str, limit: int = 3) -> List[Dict]:
        if not HAS_GOOGLE or not HAS_BS4:
            return []
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
                except Exception:
                    results.append({'title': "Web Result", 'snippet': f"Web page about {query}", 'url': url, 'source': 'web'})
            return results
        except Exception:
            return []


# ========== RESEARCH SYSTEM ==========
class ResearchSystem:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent if Path(__file__).parent.name != '' else Path(__file__).parent
        self.db_path = self.base_dir / "data" / "knowledge_base.db"
        self.db = None
        self.web_searcher = WebSearchModule()
        self._initialize()

    def _initialize(self):
        try:
            if not self.db_path.exists():
                # Try alternative paths
                alt_paths = [
                    Path("data/knowledge_base.db"),
                    Path("./data/knowledge_base.db"),
                    Path(__file__).parent / "data" / "knowledge_base.db",
                ]
                for p in alt_paths:
                    if p.exists():
                        self.db_path = p
                        break
                else:
                    return False
            self.db = ThreadSafeDatabase(str(self.db_path))
            self.db.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Init error: {e}")
            return False

    def get_database_stats(self):
        if not self.db:
            return {'total_documents': 0, 'geocoded_locations': 25}
        try:
            total = self.db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            return {'total_documents': total, 'geocoded_locations': 25}
        except Exception:
            return {'total_documents': 0, 'geocoded_locations': 0}

    def get_all_documents(self, limit=None):
        if not self.db:
            return []
        try:
            q = "SELECT * FROM documents ORDER BY id"
            if limit:
                q += f" LIMIT {limit}"
            rows = self.db.execute(q).fetchall()
            return [dict(r) for r in rows]
        except Exception:
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
        except Exception:
            return []

    def get_map_locations(self):
        locations = [
            {'name': 'Nanjing', 'lat': 32.06, 'lon': 118.80, 'year': 1368, 'event': 'Early Ming capital established'},
            {'name': 'Beijing', 'lat': 39.90, 'lon': 116.41, 'year': 1403, 'event': 'Capital moved to Beijing'},
            {'name': 'Champa', 'lat': 10.82, 'lon': 106.63, 'year': 1405, 'event': 'Southeast Asian ally'},
            {'name': 'Calicut', 'lat': 11.26, 'lon': 75.78, 'year': 1406, 'event': 'Zheng He fleet first arrived'},
            {'name': 'Sumatra', 'lat': -0.59, 'lon': 101.34, 'year': 1407, 'event': 'Strategic trading post established'},
            {'name': 'Java', 'lat': -7.61, 'lon': 110.71, 'year': 1407, 'event': 'Diplomatic missions conducted'},
            {'name': 'Siam', 'lat': 13.74, 'lon': 100.52, 'year': 1408, 'event': 'Diplomatic relations established'},
            {'name': 'Malacca', 'lat': 2.19, 'lon': 102.25, 'year': 1409, 'event': 'Strategic port established'},
            {'name': 'Sri Lanka', 'lat': 7.87, 'lon': 80.77, 'year': 1409, 'event': 'Trilingual inscription erected'},
            {'name': 'Hormuz', 'lat': 27.16, 'lon': 56.28, 'year': 1414, 'event': 'Persian Gulf trade route opened'},
            {'name': 'Aden', 'lat': 12.79, 'lon': 45.02, 'year': 1417, 'event': 'Arabian Peninsula contact made'},
            {'name': 'Mombasa', 'lat': -4.04, 'lon': 39.67, 'year': 1418, 'event': 'East African trade commenced'},
            {'name': 'Mogadishu', 'lat': 2.05, 'lon': 45.32, 'year': 1418, 'event': 'Somali coast exploration'},
            {'name': 'Zanzibar', 'lat': -6.17, 'lon': 39.20, 'year': 1419, 'event': 'Trade agreements established'},
        ]
        timeline = sorted(
            [{'year': l['year'], 'location': l['name'], 'event': l['event']} for l in locations],
            key=lambda x: x['year']
        )
        return {'locations': locations, 'timeline_events': timeline}

    def generate_intelligent_answer(self, question, doc_results, web_results, mode):
        sources = []
        if not doc_results and not web_results:
            return "I could not find specific information about that in our historical database or on the web. Please try rephrasing your question.", []

        use_docs = mode in ['Auto (Documents + Web)', 'Documents Only']
        use_web = mode in ['Auto (Documents + Web)', 'Web Only']

        if use_docs and doc_results:
            sources.append('documents')
        if use_web and web_results:
            sources.append('web')
        if not sources:
            return "No information available with current search settings.", []

        # Try GPT-4o-mini
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
Answer the following question in clear, fluent UK English. Synthesise the information into a coherent, well-structured response.

Question: {question}

Available information:
{doc_context}
{web_context}

Provide a comprehensive answer that:
1. Directly addresses the question
2. Presents key facts and historical context
3. Uses professional academic tone
4. Is written in proper UK English
"""
                resp = self.web_searcher.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional historian specialising in early Chinese maritime exploration. Write in clear, academic UK English."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7
                )
                if resp and resp.choices:
                    answer = resp.choices[0].message.content
                    answer = re.sub(r'https?://\S+', '', answer)
                    return answer, sources
            except Exception as e:
                print(f"OpenAI error: {e}")

        # Fallback
        key_points = []
        if use_docs and doc_results:
            for d in doc_results[:3]:
                content = d.get('snippet', d.get('content', ''))[:200]
                content = re.sub(r'https?://\S+', '', content).strip()
                if len(content) > 50:
                    key_points.append(content)
        if use_web and web_results:
            for w in web_results[:2]:
                content = w.get('snippet', '')[:200]
                content = re.sub(r'https?://\S+', '', content).strip()
                if len(content) > 50:
                    key_points.append(content)

        parts = [f"Regarding {question.lower().replace('?', '')}, historical evidence suggests the following."]
        for i, kp in enumerate(key_points[:3]):
            connector = ["", "\n\nFurthermore, ", "\n\nAdditionally, "][min(i, 2)]
            parts.append(connector + kp)
        parts.append("\n\nThese findings demonstrate the significance of Chinese maritime exploration during this period.")

        return ''.join(parts), sources

    def perform_search(self, question):
        start = time.time()
        mode = st.session_state.get('search_mode', 'Auto (Documents + Web)')
        docs, web = [], []

        if mode in ['Auto (Documents + Web)', 'Documents Only']:
            docs = self.search_documents(question, 10)
        if mode in ['Auto (Documents + Web)', 'Web Only']:
            if mode == 'Web Only' or not docs:
                web = self.web_searcher.search_google(question, 3)

        answer, sources = self.generate_intelligent_answer(question, docs, web, mode)

        a = st.session_state.search_analytics
        a['total_searches'] += 1
        today = datetime.now().strftime("%Y-%m-%d")
        a['searches_by_day'][today] = a['searches_by_day'].get(today, 0) + 1
        a['response_times'].append(time.time() - start)
        if len(a['response_times']) > 500:
            a['response_times'] = a['response_times'][-500:]

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


# ========== PAGE: DASHBOARD ==========
def show_dashboard(system):
    st.markdown('<div class="brand-title">1421 Foundation AI Research System</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Historical Maritime Research Platform</div>', unsafe_allow_html=True)

    stats = system.get_database_stats()
    cols = st.columns(4)
    cols[0].metric("Total Documents", stats['total_documents'])
    cols[1].metric("Chat Sessions", len(st.session_state.chat_sessions))
    cols[2].metric("Geocoded Locations", stats['geocoded_locations'])
    cols[3].metric("Database Status", "Active" if system.db else "Inactive")

    st.divider()

    st.markdown("""
    <div class="how-to-use">
        <h3 style="font-family: 'Cinzel', serif; color: #2c3e50;">HOW TO USE</h3>
        <ul>
            <li><strong>Chat:</strong> Use the chat interface to ask questions. Sessions are saved automatically.</li>
            <li><strong>Documents:</strong> Browse and search the historical document database.</li>
            <li><strong>Voyage Map:</strong> Visualise routes on an interactive map with timeline.</li>
            <li><strong>Analytics:</strong> Track your research patterns and statistics.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<h3 style="font-family: \'Cinzel\', serif; color: #2c3e50; margin-top: 20px;">Example Questions</h3>', unsafe_allow_html=True)

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
                # FIXED: Create new chat and properly set the question
                new_id = len(st.session_state.chat_sessions)
                words = q.strip().split()
                summary = ' '.join(words[:6]) + ('...' if len(words) > 6 else '')
                st.session_state.chat_sessions.append({
                    'id': new_id, 'name': summary, 'history': [],
                    'created': datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.session_state.current_chat_id = new_id
                st.session_state.current_question = q
                st.session_state.auto_search = True
                st.session_state.current_page = 'chat'
                st.rerun()


# ========== PAGE: CHAT ==========
def show_chat_page(system):
    current_chat_id = st.session_state.current_chat_id
    current_session = next((s for s in st.session_state.chat_sessions if s['id'] == current_chat_id), None)

    if not current_session:
        current_session = st.session_state.chat_sessions[0]
        st.session_state.current_chat_id = current_session['id']

    chat_history = current_session['history']

    # Two-column layout: chat + history panel
    chat_col, history_col = st.columns([3, 1])

    with history_col:
        st.markdown(f'<div class="chat-history-header">Chat History</div>', unsafe_allow_html=True)

        if st.button("+ New Chat", key="new_chat_main", use_container_width=True):
            new_id = len(st.session_state.chat_sessions)
            st.session_state.chat_sessions.append({
                'id': new_id, 'name': 'New Chat', 'history': [],
                'created': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.session_state.current_chat_id = new_id
            st.rerun()

        st.markdown("---")

        for session in reversed(st.session_state.chat_sessions[-20:]):
            is_active = session['id'] == current_chat_id
            prefix = "▶ " if is_active else ""
            label = f"{prefix}{session['name']}"

            c1, c2 = st.columns([4, 1])
            with c1:
                if st.button(label, key=f"chat_sel_{session['id']}", use_container_width=True):
                    st.session_state.current_chat_id = session['id']
                    st.rerun()
            with c2:
                if len(st.session_state.chat_sessions) > 1:
                    if st.button("🗑", key=f"chat_del_{session['id']}"):
                        st.session_state.chat_sessions = [s for s in st.session_state.chat_sessions if s['id'] != session['id']]
                        if st.session_state.current_chat_id == session['id']:
                            st.session_state.current_chat_id = st.session_state.chat_sessions[-1]['id']
                        st.rerun()

    with chat_col:
        st.markdown(f'<div class="sub-header">{current_session["name"]}</div>', unsafe_allow_html=True)

        # Check for auto-search from example questions
        if st.session_state.auto_search and st.session_state.current_question:
            question = st.session_state.current_question
            st.session_state.auto_search = False
        else:
            question = st.session_state.current_question

        # Chat messages in a scrollable container
        chat_container = st.container(height=500)
        with chat_container:
            if not chat_history:
                st.markdown("""
                <div style="text-align: center; padding: 40px; color: #888;">
                    <h3 style="font-family: 'Cinzel', serif; color: #2c3e50;">Welcome</h3>
                    <p>Ask any question about Chinese exploration, Zheng He's voyages, or the 1421 theory.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                for chat in chat_history:
                    st.markdown(f'<div class="chat-message user-message"><strong>You:</strong><br>{chat["question"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="chat-message assistant-message"><strong>1421 AI:</strong><br>{chat["answer"]}</div>', unsafe_allow_html=True)
                    badges = ""
                    if 'documents' in chat.get('sources_used', []):
                        badges += '<span class="source-badge badge-document">Documents</span>'
                    if 'web' in chat.get('sources_used', []):
                        badges += '<span class="source-badge badge-web">Web</span>'
                    if badges:
                        st.markdown(badges, unsafe_allow_html=True)

                    with st.expander("Sources", expanded=False):
                        for res in chat.get('document_results', [])[:3]:
                            st.markdown(f"**{res.get('title', 'Unknown')}**")
                            if res.get('snippet'):
                                st.info(res['snippet'][:200])
                        for res in chat.get('web_results', [])[:2]:
                            st.markdown(f"**{res.get('title', 'Unknown')}**")
                            if res.get('url'):
                                st.markdown(f"[View]({res['url']})")

        # Input at bottom - always visible
        st.markdown("---")
        input_col, btn_col = st.columns([5, 1])
        with input_col:
            question_input = st.text_input(
                "Ask a question",
                value=question if question else "",
                key="chat_q",
                label_visibility="collapsed",
                placeholder="Ask about Chinese exploration, Zheng He, or the 1421 theory..."
            )
        with btn_col:
            ask = st.button("Research", type="primary", key="chat_ask", use_container_width=True)

        if (ask or (question and st.session_state.auto_search)) and question_input:
            with st.spinner("Researching..."):
                result = system.perform_search(question_input)
                for session in st.session_state.chat_sessions:
                    if session['id'] == st.session_state.current_chat_id:
                        session['history'].append(result)
                        # Always update name to a summary of the latest question
                        words = question_input.strip().split()
                        summary = ' '.join(words[:6]) + ('...' if len(words) > 6 else '')
                        session['name'] = summary
                        break
                st.session_state.current_question = ""
                st.rerun()


# ========== PAGE: DOCUMENTS ==========
def show_documents_page(system):
    st.markdown('<div class="sub-header">Research Documents</div>', unsafe_allow_html=True)

    search = st.text_input("", placeholder="Search documents by title, author, or keywords...",
                           label_visibility="collapsed", key="doc_search")

    c1, c2, c3 = st.columns([1, 2, 2])
    with c1:
        limit_map = {"All": None, "25": 25, "50": 50, "100": 100}
        limit = limit_map[st.selectbox("Show", list(limit_map.keys()), index=0, label_visibility="collapsed")]
    with c2:
        search_btn = st.button("SEARCH", key="search_docs", use_container_width=True)
    with c3:
        show_btn = st.button("SHOW ALL", key="show_docs", use_container_width=True)

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
        st.info("Enter a search query or click 'SHOW ALL'.")

    if docs:
        df = pd.DataFrame([{
            'ID': d.get('id', ''),
            'Title': d.get('title', 'Untitled')[:60],
            'Author': d.get('author', 'Unknown')[:30],
            'Type': d.get('source_type', 'Unknown'),
            'Words': d.get('word_count', 0),
        } for d in docs])
        st.dataframe(df, use_container_width=True, height=500, hide_index=True)
        csv = df.to_csv(index=False).encode()
        st.download_button("DOWNLOAD CSV", csv, f"documents_{datetime.now():%Y%m%d}.csv", "text/csv", use_container_width=True)


# ========== PAGE: MAP ==========
def show_map_page(system):
    st.markdown('<div class="sub-header">Voyage Map</div>', unsafe_allow_html=True)

    map_data = system.get_map_locations()
    locations = map_data['locations']
    timeline = map_data['timeline_events']

    # Controls
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    with c1:
        year = st.slider("Year", 1368, 1421, st.session_state.current_year, key="map_slider")
        st.session_state.current_year = year
    with c2:
        if st.button("▶ Play", key="play_map", use_container_width=True):
            st.session_state.animation_playing = True
    with c3:
        if st.button("⏸ Pause", key="pause_map", use_container_width=True):
            st.session_state.animation_playing = False
    with c4:
        if st.button("↺ Reset", key="reset_map", use_container_width=True):
            st.session_state.current_year = 1368
            st.session_state.animation_playing = False
            st.rerun()

    # FIXED: Animation logic - runs continuously when playing
    if st.session_state.animation_playing:
        if st.session_state.current_year < 1421:
            st.session_state.current_year += 1
            time.sleep(0.8)
            st.rerun()
        else:
            st.session_state.animation_playing = False

    filtered = [l for l in locations if l['year'] <= st.session_state.current_year]

    # REMOVED: Fullscreen checkbox - no longer needed
    map_height = 500  # Fixed height

    if HAS_FOLIUM:
        # Real interactive map with folium
        m = folium.Map(location=[15, 80], zoom_start=3, tiles='CartoDB positron')

        # Route line
        if len(filtered) > 1:
            sorted_locs = sorted(filtered, key=lambda x: x['year'])
            route_coords = [[l['lat'], l['lon']] for l in sorted_locs]
            folium.PolyLine(route_coords, color='#d4af37', weight=3, opacity=0.8, dash_array='10').add_to(m)

        # Markers
        for loc in filtered:
            folium.CircleMarker(
                location=[loc['lat'], loc['lon']],
                radius=8,
                color='#d4af37',
                fill=True,
                fill_color='#d4af37',
                fill_opacity=0.8,
                popup=folium.Popup(f"<b>{loc['name']}</b><br>{loc['year']}<br>{loc['event']}", max_width=250),
                tooltip=loc['name']
            ).add_to(m)

        st_folium(m, width=None, height=map_height, use_container_width=True)
    else:
        # Plotly geo fallback - proper world map
        fig = go.Figure()

        if filtered:
            sorted_f = sorted(filtered, key=lambda x: x['year'])
            lats = [l['lat'] for l in sorted_f]
            lons = [l['lon'] for l in sorted_f]
            names = [l['name'] for l in sorted_f]
            years = [l['year'] for l in sorted_f]
            events = [l['event'] for l in sorted_f]

            # Route
            if len(sorted_f) > 1:
                fig.add_trace(go.Scattergeo(
                    lon=lons, lat=lats, mode='lines',
                    line=dict(width=2.5, color='#d4af37', dash='dash'),
                    name='Route', hoverinfo='none'
                ))

            # Markers
            fig.add_trace(go.Scattergeo(
                lon=lons, lat=lats, mode='markers+text',
                marker=dict(size=10, color=years, colorscale='YlOrBr',
                            colorbar=dict(title="Year"), line=dict(width=1, color='white')),
                text=names, textposition="top center", name='Locations',
                customdata=events,
                hovertemplate='%{text}<br>Year: %{marker.color}<br>%{customdata}<extra></extra>'
            ))

        fig.update_layout(
            geo=dict(
                showland=True, landcolor='rgb(243,243,243)',
                coastlinecolor='rgb(180,180,180)', showcountries=True,
                countrycolor='rgb(200,200,200)', showocean=True,
                oceancolor='rgb(220,235,250)', projection_type='natural earth',
                center=dict(lat=15, lon=80),
                lataxis=dict(range=[-20, 50]), lonaxis=dict(range=[30, 140])
            ),
            height=map_height, margin=dict(l=0, r=0, t=10, b=0), showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    # Timeline - ADDED back
    st.divider()
    st.markdown(f'<h3 style="font-family: \'Cinzel\', serif;">Historical Timeline (to {st.session_state.current_year})</h3>', unsafe_allow_html=True)
    
    filtered_events = [e for e in timeline if e['year'] <= st.session_state.current_year]
    
    # Create a nice timeline display
    for ev in filtered_events:
        st.markdown(f"""
        <div style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #d4af37; border-radius: 4px;">
            <strong style="font-size: 1.1rem; color: #d4af37;">{ev['year']}</strong> — <strong>{ev['location']}</strong>: {ev['event']}
        </div>
        """, unsafe_allow_html=True)


# ========== PAGE: ANALYTICS ==========
def show_analytics_page(system):
    st.markdown('<div class="sub-header">Analytics Dashboard</div>', unsafe_allow_html=True)

    a = st.session_state.search_analytics
    stats = system.get_database_stats()

    cols = st.columns(4)
    cols[0].metric("Total Searches", a['total_searches'])
    avg_time = sum(a['response_times']) / max(1, len(a['response_times']))
    cols[1].metric("Avg Response Time", f"{avg_time:.2f}s")
    cols[2].metric("Active Days", len(a['searches_by_day']))
    cols[3].metric("Chat Sessions", len(st.session_state.chat_sessions))

    if a['sources_used']:
        st.subheader("Source Usage")
        c1, c2, c3 = st.columns(3)
        c1.metric("Document Searches", a['sources_used']['documents'])
        c2.metric("Web Searches", a['sources_used']['web'])
        c3.metric("Combined Searches", a['sources_used']['both'])

    if a['searches_by_day']:
        st.subheader("Searches by Day")
        df = pd.DataFrame(list(a['searches_by_day'].items()), columns=['Date', 'Count'])
        fig = px.bar(df, x='Date', y='Count', color_discrete_sequence=['#d4af37'])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)


# ========== PAGE: FEEDBACK ==========
def show_feedback_page():
    st.markdown('<div class="sub-header">Send Feedback</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Your Name", placeholder="Optional")
    with c2:
        email = st.text_input("Email Address", placeholder="Required")

    feedback_type = st.selectbox("Feedback Type", ["Bug Report", "Feature Request", "Suggestion", "Question", "Other"])
    message = st.text_area("Your Message", placeholder="Describe your issue or suggestion...", height=150)

    if st.button("SUBMIT FEEDBACK", type="primary", use_container_width=True):
        if not email:
            st.error("Email is required")
        elif not message:
            st.error("Message is required")
        else:
            if 'feedback_history' not in st.session_state:
                st.session_state.feedback_history = []
            st.session_state.feedback_history.append({
                'timestamp': datetime.now().isoformat(), 'name': name or "Anonymous",
                'email': email, 'message': message, 'type': feedback_type
            })
            st.success("Thank you for your feedback!")


# ========== PAGE: SETTINGS ==========
def show_settings_page(system):
    st.markdown('<div class="sub-header">System Settings</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Database")
        stats = system.get_database_stats()
        st.write(f"**Documents:** {stats['total_documents']}")
        st.write(f"**Locations:** {stats['geocoded_locations']}")
    with c2:
        st.subheader("System Status")
        st.write(f"**Database:** {'Active' if system.db else 'Inactive'}")
        st.write(f"**Web Search:** {'Active' if HAS_GOOGLE else 'Inactive'}")
        openai_status = 'Active' if (system.web_searcher.openai_client) else 'Inactive'
        st.write(f"**GPT-4o-mini:** {openai_status}")

    st.divider()
    st.subheader("Search Mode")
    mode = st.radio("Select search mode:", ["Auto (Documents + Web)", "Documents Only", "Web Only"],
                    index=0, horizontal=True)
    st.session_state.search_mode = mode

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("CLEAR CHAT HISTORY", use_container_width=True):
            st.session_state.chat_sessions = [{'id': 0, 'name': 'New Chat', 'history': [],
                                                'created': datetime.now().strftime("%Y-%m-%d %H:%M")}]
            st.session_state.current_chat_id = 0
            st.success("Chat history cleared!")
            st.rerun()
    with c2:
        if st.button("RESET ANALYTICS", use_container_width=True):
            st.session_state.search_analytics = {
                'total_searches': 0, 'searches_by_day': {}, 'searches_by_hour': {},
                'questions_asked': [], 'response_times': [], 'popular_topics': {},
                'user_sessions': [], 'sources_used': {'documents': 0, 'web': 0, 'both': 0}
            }
            st.success("Analytics reset!")
            st.rerun()


# ========== NAVIGATION ==========
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="brand-title" style="font-size:1.4rem;">1421 Foundation AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-subtitle" style="font-size:0.65rem;">Research System</div>', unsafe_allow_html=True)

        pages = [
            ("🏠  DASHBOARD", "dashboard"),
            ("💬  CHAT", "chat"),
            ("📄  DOCUMENTS", "documents"),
            ("🗺️  VOYAGE MAP", "map"),
            ("📊  ANALYTICS", "analytics"),
            ("✉️  FEEDBACK", "feedback"),
            ("⚙️  SETTINGS", "settings"),
        ]

        for label, pid in pages:
            btn_type = "primary" if st.session_state.current_page == pid else "secondary"
            if st.button(label, key=f"nav_{pid}", use_container_width=True, type=btn_type):
                st.session_state.current_page = pid
                st.rerun()
        
        # REMOVED: Close navigation button


# ========== MAIN ==========
@st.cache_resource
def init_system():
    return ResearchSystem()


def main():
    system = init_system()

    # Always show navigation (no close button)
    render_sidebar()

    # Route pages
    page = st.session_state.current_page
    if page == "dashboard":
        show_dashboard(system)
    elif page == "chat":
        show_chat_page(system)
    elif page == "documents":
        show_documents_page(system)
    elif page == "map":
        show_map_page(system)
    elif page == "analytics":
        show_analytics_page(system)
    elif page == "feedback":
        show_feedback_page()
    elif page == "settings":
        show_settings_page(system)


if __name__ == "__main__":
    main()
