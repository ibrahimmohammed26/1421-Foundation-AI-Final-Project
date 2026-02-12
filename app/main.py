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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    'feedback_submitted': False
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ========== CSS STYLING (Optimized) ==========
st.markdown("""
<style>
/* Main styling */
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
.main .block-container { background: rgba(255,255,255,0.98); border-radius: 15px; padding: 2.5rem; margin-top: 1rem; box-shadow: 0 6px 20px rgba(0,0,0,0.1); }

/* Headers */
.main-header { font-size: 3rem; color: #000; text-align: center; margin-bottom: 1rem; font-weight: 800; background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.sub-header { font-size: 1.8rem; color: #2c3e50; margin-bottom: 1.5rem; font-weight: 700; border-bottom: 3px solid #d4af37; padding-bottom: 0.5rem; }

/* Sidebar */
section[data-testid="stSidebar"] > div { background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%) !important; border-right: 4px solid #d4af37; padding-top: 2rem !important; }

/* Navigation */
.sidebar-button { display: block; background: transparent; color: white !important; font-size: 1.2rem; font-weight: 600; padding: 0.8rem 1rem; text-align: left; border-radius: 8px; transition: all 0.3s ease; cursor: pointer; margin: 5px 0; border: none; width: 100%; text-transform: uppercase; letter-spacing: 0.5px; }
.sidebar-button:hover { background: rgba(212,175,55,0.2); transform: translateX(5px); border-left: 3px solid #d4af37; }
.sidebar-button.active { background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%); color: #000 !important; font-weight: 700; }

/* Status popup */
.popup-notification { position: fixed; top: 100px; right: 20px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 18px 25px; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.3); z-index: 1000; animation: slideInRight 0.5s ease, fadeOut 0.5s ease 4.5s forwards; border-left: 5px solid #fff; max-width: 400px; }
@keyframes slideInRight { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
@keyframes fadeOut { from { opacity: 1; } to { opacity: 0; transform: translateY(-20px); } }

/* Source badges */
.source-badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; margin-right: 8px; margin-bottom: 8px; }
.badge-document { background: #4a6491; color: white; }
.badge-web { background: #28a745; color: white; }

/* Metrics */
[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; color: #2c3e50 !important; }
[data-testid="stMetricLabel"] { font-weight: 600 !important; font-size: 1rem !important; color: #d4af37 !important; }

/* Buttons */
.stButton > button { background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%); color: white !important; border: none !important; border-radius: 10px; font-weight: 600 !important; font-size: 1.1rem !important; padding: 12px 24px !important; transition: all 0.3s ease !important; }
.stButton > button:hover { background: linear-gradient(135deg, #b8860b 0%, #8b4513 100%); transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.2); }

/* Saved searches */
.saved-search-sidebar-item { background: rgba(255,255,255,0.1); border-radius: 8px; padding: 12px; margin: 8px 0; border-left: 4px solid #d4af37; cursor: pointer; transition: all 0.3s ease; }
.saved-search-sidebar-item:hover { background: rgba(255,255,255,0.2); transform: translateX(5px); }
.search-time { font-size: 0.8rem; color: #ccc; margin-top: 5px; }
.search-query { font-size: 0.9rem; color: #fff; margin-bottom: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Answer display */
.answer-text { font-size: 1.1rem; line-height: 1.8; color: #333; margin: 20px 0; padding: 10px 0; }
.chat-message { padding: 20px; margin: 15px 0; border-radius: 12px; max-width: 100%; animation: fadeIn 0.3s ease; }
.user-message { background: linear-gradient(135deg, #4a6491 0%, #2c3e50 100%); color: white; margin-right: 20%; border-bottom-right-radius: 4px; }
.assistant-message { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); color: #333; border: 1px solid #ddd; margin-left: 20%; border-bottom-left-radius: 4px; }

/* Action buttons */
.action-buttons { display: flex; gap: 10px; margin-top: 15px; margin-bottom: 20px; }
.copy-button, .save-button, .feedback-button { background: linear-gradient(135deg, #6c757d 0%, #495057 100%); color: white; border: none; border-radius: 6px; padding: 8px 16px; font-size: 0.9rem; cursor: pointer; transition: all 0.3s ease; }
.save-button { background: linear-gradient(135deg, #4a6491 0%, #2c3e50 100%); }
.feedback-button { background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); margin-top: 10px; width: 100%; }
.copy-button:hover, .save-button:hover, .feedback-button:hover { transform: translateY(-2px); }

/* Delete button */
.delete-button { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; border: none; border-radius: 6px; padding: 4px 8px; font-size: 0.8rem; cursor: pointer; }

/* Headers */
.saved-searches-header, .system-status-header { color: #FFD700 !important; font-weight: 700 !important; }

/* Question input at bottom */
.question-input-container { position: sticky; bottom: 0; background: white; padding: 20px; border-top: 1px solid #ddd; margin-top: 20px; border-radius: 8px; }

/* Confirmation dialog */
.confirmation-dialog { background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px; margin: 10px 0; color: #856404; }

/* Feedback form */
.feedback-form { background: rgba(255,255,255,0.1); border-radius: 8px; padding: 15px; margin: 10px 0; }
</style>

<script>
function copyAnswerToClipboard(t) { navigator.clipboard.writeText(t).then(()=>alert('Answer copied!'), e=>console.error(e)); }
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
    """Uses google-search package (scrapes Google results)"""
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
                    results.append({'title': f"Web Result {i+1}", 'snippet': f"Web page about {query}", 'url': url, 'source': 'web'})
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
    def render_sidebar():
        saved = st.session_state.saved_searches
        st.sidebar.markdown("---")
        st.sidebar.markdown('<h3 class="saved-searches-header">SAVED SEARCHES</h3>', unsafe_allow_html=True)
        
        if saved:
            for s in saved[-5:][::-1]:
                cols = st.sidebar.columns([3, 1, 1])
                with cols[0]:
                    st.markdown(f'<div class="saved-search-sidebar-item"><div class="search-query">{s["question"][:50]}{"..." if len(s["question"])>50 else ""}</div><div class="search-time">{s["time"]} • {len(s["sources"])} sources</div></div>', unsafe_allow_html=True)
                with cols[1]:
                    if st.button("↻", key=f"sr_{s['id']}", help="Reload"):
                        st.session_state.current_question = s['question']
                        st.session_state.auto_search = True
                        st.rerun()
                with cols[2]:
                    if st.button("🗑", key=f"sd_{s['id']}", help="Delete"):
                        st.session_state.deleting_search_id = s['id']
                        st.rerun()
            
            if st.session_state.deleting_search_id:
                st.sidebar.markdown('<div class="confirmation-dialog"><strong>Delete Search?</strong><br><small>This cannot be undone.</small></div>', unsafe_allow_html=True)
                c1, c2 = st.sidebar.columns(2)
                if c1.button("Confirm", key="confirm_del"):
                    SavedSearchesSystem.delete_search(st.session_state.deleting_search_id)
                    st.session_state.deleting_search_id = None
                    st.rerun()
                if c2.button("Cancel", key="cancel_del"):
                    st.session_state.deleting_search_id = None
                    st.rerun()
            st.sidebar.markdown(f"*Showing 5 of {len(saved)}*")
        else:
            st.sidebar.markdown('<div class="no-saved-searches">No saved searches yet.<br>Searches are automatically saved.</div>', unsafe_allow_html=True)

# ========== FEEDBACK SYSTEM ==========
class FeedbackSystem:
    @staticmethod
    def send_feedback(name: str, email: str, message: str, feedback_type: str):
        """Send feedback - currently logs to console and saves to session"""
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'name': name,
            'email': email,
            'message': message,
            'type': feedback_type
        }
        
        # Store in session state
        if 'feedback_history' not in st.session_state:
            st.session_state.feedback_history = []
        st.session_state.feedback_history.append(feedback)
        
        # Log to console (in production, send to email, database, or API)
        print(f"FEEDBACK RECEIVED: {feedback}")
        
        # Here you would integrate with an email service or API
        # Examples below in the API list
        
        return True
    
    @staticmethod
    def render_feedback_form():
        with st.sidebar:
            st.markdown("---")
            st.markdown('<h3 class="system-status-header">SEND FEEDBACK</h3>', unsafe_allow_html=True)
            
            with st.expander("📝 Report Issue / Suggestion", expanded=False):
                name = st.text_input("Your Name", placeholder="Optional", key="feedback_name")
                email = st.text_input("Email", placeholder="Required", key="feedback_email")
                feedback_type = st.selectbox("Feedback Type", ["Bug Report", "Feature Request", "Suggestion", "Question", "Other"], key="feedback_type")
                message = st.text_area("Message", placeholder="Describe your issue or suggestion...", height=100, key="feedback_message")
                
                if st.button("Submit Feedback", key="submit_feedback", use_container_width=True):
                    if not email:
                        st.error("Email is required")
                    elif not message:
                        st.error("Message is required")
                    else:
                        if FeedbackSystem.send_feedback(name or "Anonymous", email, message, feedback_type):
                            st.success("Thank you for your feedback!")
                            st.session_state.feedback_submitted = True
                            time.sleep(2)
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
            self.db.execute("SELECT 1")  # Test connection
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
    
    def get_all_documents(self, limit=None, source_type=None):
        if not self.db:
            return []
        try:
            q = "SELECT * FROM documents"
            params = []
            if source_type and source_type != "All":
                q += " WHERE source_type = ?"
                params.append(source_type)
            q += " ORDER BY id"
            if limit:
                q += " LIMIT ?"
                params.append(limit)
            rows = self.db.execute(q, params).fetchall()
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
                    
                    # Find snippet
                    lower = content.lower()
                    snippet = ""
                    for w in words:
                        if w in lower:
                            idx = lower.find(w)
                            start = max(0, idx - 100)
                            end = min(len(content), idx + 200)
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
    
    def generate_answer(self, question, doc_results, web_results):
        sources = []
        combined = []
        
        if doc_results:
            sources.append('documents')
            for d in doc_results[:2]:
                if d.get('snippet'):
                    combined.append(f"**From historical documents ({d.get('title', 'Unknown')}):** {d['snippet'].replace(chr(10), ' ').strip()}")
        
        if web_results:
            sources.append('web')
            for w in web_results[:2]:
                if w.get('snippet'):
                    combined.append(f"**From web research ({w.get('title', 'Unknown')}):** {w['snippet'].replace(chr(10), ' ').strip()}")
        
        if not doc_results and not web_results:
            return "I couldn't find specific information about that. Try rephrasing your question or using different keywords.", []
        
        if self.web_searcher.openai_client:
            try:
                doc_text = ' '.join([d.get('snippet', '')[:300] for d in doc_results[:2]])
                web_text = ' '.join([w.get('snippet', '')[:300] for w in web_results[:2]])
                prompt = f"Question: {question}\n\nDocuments: {doc_text}\n\nWeb: {web_text}\n\nProvide a comprehensive answer based on this information. Do not include URLs in the main text."
                resp = self.web_searcher.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "You are a historical research assistant specializing in Chinese exploration history."},
                             {"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.7
                )
                if resp:
                    return re.sub(r'https?://\S+', '', resp.choices[0].message.content), sources
            except:
                pass
        
        # Fallback
        base = random.choice([
            f"Based on historical research, {question.replace('?', '').strip()} can be understood through multiple sources.\n\n",
            f"Research indicates that {question.replace('?', '').strip()} reveals several important findings.\n\n"
        ])
        if combined:
            base += "\n\n".join(combined)
            if len(sources) > 1:
                base += "\n\n**Sources:** This information comes from both historical documents and current web research."
            elif 'documents' in sources:
                base += "\n\n**Sources:** This evidence primarily comes from historical documents in the 1421 research database."
            else:
                base += "\n\n**Sources:** This information comes from web-based historical research."
        return base, sources
    
    def perform_search(self, question):
        start = time.time()
        docs = self.search_documents(question, 10)
        time.sleep(0.3)
        web = self.web_searcher.search_google(question, 3) if not docs else []
        answer, sources = self.generate_answer(question, docs, web)
        
        # Track analytics
        a = st.session_state.search_analytics
        a['total_searches'] += 1
        today = datetime.now().strftime("%Y-%m-%d")
        a['searches_by_day'][today] = a['searches_by_day'].get(today, 0) + 1
        a['response_times'].append(time.time() - start)
        if len(a['response_times']) > 500:
            a['response_times'] = a['response_times'][-500:]
        
        return {
            'question': question, 'answer': answer, 'sources_used': sources,
            'document_results': docs, 'web_results': web,
            'total_results': len(docs) + len(web)
        }

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
    st.markdown('<h2 class="sub-header">ASK HISTORICAL QUESTIONS</h2>', unsafe_allow_html=True)
    
    # Example questions
    examples = [
        "Zheng He voyages significance",
        "Chinese ships in America before Columbus",
        "Ming Dynasty naval technology",
        "Chinese treasure fleets purpose",
        "Chinese navigation vs European methods"
    ]
    cols = st.columns(2)
    for i, q in enumerate(examples):
        with cols[i % 2]:
            if st.button(q, key=f"ex_{i}", use_container_width=True):
                st.session_state.current_question = q
                st.session_state.auto_search = True
                st.rerun()
    
    st.divider()
    
    # Chat history
    for chat in st.session_state.chat_history[-20:]:  # Limit to last 20
        st.markdown(f'<div class="chat-message user-message"><strong>You:</strong><br>{chat["question"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-message assistant-message"><strong>1421 AI:</strong><br><div class="answer-text">{chat["answer"].replace(chr(10), "<br>")}</div></div>', unsafe_allow_html=True)
        
        # Action buttons
        st.markdown(f'<div class="action-buttons"><button class="copy-button" onclick="copyAnswerToClipboard(`{chat["answer"].replace("`", "'").replace(chr(10), "\\n")}`)">Copy Answer</button></div>', unsafe_allow_html=True)
        
        # Sources
        st.markdown("**Sources used:**")
        if 'documents' in chat['sources_used']:
            st.markdown('<span class="source-badge badge-document">Documents</span>', unsafe_allow_html=True)
        if 'web' in chat['sources_used']:
            st.markdown('<span class="source-badge badge-web">Web</span>', unsafe_allow_html=True)
        
        with st.expander(f"DETAILED SOURCES ({chat['total_results']} results)", expanded=False):
            for res in chat.get('document_results', [])[:3]:
                st.markdown(f"**{res.get('title', 'Unknown')}**")
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
    
    # Question input at bottom
    st.markdown('<div class="question-input-container">', unsafe_allow_html=True)
    col1, col2 = st.columns([4, 1])
    with col1:
        q = st.text_input("", value=st.session_state.current_question, placeholder="Type your question here...", key="q_input", label_visibility="collapsed")
    with col2:
        ask = st.button("RESEARCH", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if (ask or st.session_state.auto_search) and q:
        st.session_state.auto_search = False
        with st.spinner("Researching..."):
            result = system.perform_search(q)
            st.session_state.chat_history.append(result)
            SavedSearchesSystem.save_search(q, result['answer'], result['sources_used'], 
                                          result['document_results'], result['web_results'])
            st.rerun()

def show_documents_page(system):
    st.markdown('<h2 class="sub-header">RESEARCH DOCUMENTS</h2>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        search = st.text_input("", placeholder="Search documents...", label_visibility="collapsed")
    with c2:
        filter_type = st.selectbox("", ["All", "Book", "Article", "Research Paper", "Website"], label_visibility="collapsed")
    with c3:
        limit_opts = {"25": 25, "50": 50, "100": 100, "All": None}
        limit = limit_opts[st.selectbox("Show", ["All", "25", "50", "100"], index=0, label_visibility="collapsed")]
    
    c1, c2 = st.columns(2)
    search_btn = c1.button("SEARCH", type="primary", use_container_width=True)
    show_btn = c2.button("SHOW DOCUMENTS", use_container_width=True)
    
    docs = []
    if search_btn and search:
        docs = system.search_documents(search, limit or 1000)
        if docs:
            st.success(f"Found {len(docs)} documents")
    elif show_btn:
        docs = system.get_all_documents(limit, filter_type if filter_type != "All" else None)
        if docs:
            st.success(f"Loaded {len(docs)} documents")
    else:
        st.info("Enter a search query or click 'SHOW DOCUMENTS' to load all documents.")
    
    if docs:
        df = pd.DataFrame([{
            'ID': d.get('id', ''), 'Title': d.get('title', 'Untitled')[:50],
            'Author': d.get('author', 'Unknown')[:30], 'Type': d.get('source_type', 'Unknown'),
            'Words': d.get('word_count', 0)
        } for d in docs])
        st.dataframe(df, column_config={"ID": "ID", "Title": "Title", "Author": "Author", 
                                       "Type": "Type", "Words": "Words"}, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode()
        st.download_button("DOWNLOAD CSV", csv, f"docs_{datetime.now():%Y%m%d}.csv", "text/csv")

def show_map_page(system):
    st.markdown('<h2 class="sub-header">FULL VOYAGE MAP</h2>', unsafe_allow_html=True)
    st.info("Map visualization will be implemented with actual coordinate data from your database.")

def show_analytics_page(system):
    st.markdown('<h2 class="sub-header">ANALYTICS DASHBOARD</h2>', unsafe_allow_html=True)
    a = st.session_state.search_analytics
    st.metric("Total Searches", a['total_searches'])
    if a['response_times']:
        st.metric("Avg Response Time", f"{sum(a['response_times'])/len(a['response_times']):.2f}s")

def show_settings_page(system):
    st.markdown('<h2 class="sub-header">SYSTEM SETTINGS</h2>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Database")
        stats = system.get_database_stats()
        st.write(f"**Documents:** {stats['total_documents']}")
        st.write(f"**Saved Searches:** {stats['saved_searches']}")
    with c2:
        st.subheader("System")
        st.write(f"**Database:** {'Active' if system.db else 'Inactive'}")
        st.write(f"**Web Search:** {'Active' if system.web_searcher else 'Inactive'}")
    
    st.divider()
    if st.button("CLEAR CHAT HISTORY", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    if st.button("CLEAR ALL SAVED SEARCHES", use_container_width=True):
        st.session_state.saved_searches = []
        st.rerun()

# ========== SIDEBAR ==========
def render_sidebar():
    with st.sidebar:
        st.markdown('<div style="text-align: center; margin-bottom: 2rem;"><h2 style="color: #d4af37; font-size: 1.8rem;">1421 AI</h2><p style="color: #fff; opacity: 0.8;">HISTORICAL RESEARCH SYSTEM</p></div>', unsafe_allow_html=True)
        
        # Navigation
        pages = [("DASHBOARD", "dashboard"), ("RESEARCH DOCUMENTS", "documents"), 
                ("FULL VOYAGE MAP", "map"), ("ANALYTICS", "analytics"), ("SETTINGS", "settings")]
        for label, pid in pages:
            if st.button(label, key=f"nav_{pid}", use_container_width=True, 
                        type="primary" if st.session_state.current_page == pid else "secondary"):
                st.session_state.current_page = pid
                st.rerun()
        
        # Feedback button (above settings)
        st.sidebar.markdown("---")
        if st.sidebar.button("📧 SEND FEEDBACK", key="feedback_nav", use_container_width=True):
            st.session_state.current_page = "feedback"
            st.rerun()
        
        # Saved searches
        SavedSearchesSystem.render_sidebar()
        
        # System status
        if 'system_stats' in st.session_state:
            stats = st.session_state.system_stats
            st.sidebar.markdown("---")
            st.sidebar.markdown('<h3 class="system-status-header">SYSTEM STATUS</h3>', unsafe_allow_html=True)
            st.sidebar.markdown(f'<div style="background:rgba(255,255,255,0.1);padding:15px;border-radius:10px;"><p style="color:#FFD700;"><strong>Documents:</strong> <span style="color:white;">{stats.get("total_documents",0)}</span></p><p style="color:#FFD700;"><strong>Saved:</strong> <span style="color:white;">{stats.get("saved_searches",0)}</span></p><p style="color:#FFD700;"><strong>Chat:</strong> <span style="color:white;">{len(st.session_state.chat_history)}</span></p></div>', unsafe_allow_html=True)

def show_feedback_page():
    """Standalone feedback page"""
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
        if st.button("📤 SUBMIT FEEDBACK", type="primary", use_container_width=True):
            if not email:
                st.error("Email is required")
            elif not message:
                st.error("Message is required")
            else:
                if FeedbackSystem.send_feedback(name or "Anonymous", email, message, feedback_type):
                    st.success("✅ Thank you for your feedback! We'll review it shortly.")
                    st.balloons()
                    st.session_state.feedback_submitted = True
    
    with col3:
        if st.button("← BACK TO DASHBOARD", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()
    
    # Show recent feedback if submitted
    if st.session_state.get('feedback_submitted'):
        st.divider()
        st.info("Your feedback has been recorded. Thank you for helping improve 1421 AI!")

# ========== MAIN ==========
def main():
    st.markdown('<div style="text-align: center; padding: 1rem 0 1rem 0;"><h1 class="main-header">1421 AI - HISTORICAL RESEARCH SYSTEM</h1><p style="font-size: 1.2rem; color: #666; max-width: 800px; margin: 0 auto;">A comprehensive research platform for studying Chinese exploration history and the 1421 theory</p></div>', unsafe_allow_html=True)
    
    system = init_system()
    if not system or not system.db:
        st.error("SYSTEM INITIALIZATION FAILED. Check if knowledge_base.db exists in the data folder.")
        st.stop()
    
    st.session_state.system_stats = system.get_database_stats()
    render_sidebar()
    
    # Page routing
    if st.session_state.current_page == "feedback":
        show_feedback_page()
    elif st.session_state.current_page == "dashboard":
        show_dashboard(system)
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
