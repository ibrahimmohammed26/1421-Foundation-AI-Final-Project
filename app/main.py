"""
1421 AI - Historical Research System
Professional version with analytics and saved searches
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
from datetime import datetime, timedelta
import time
import threading
import random
import sys
import os
from collections import Counter

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="1421 AI - Historical Research System",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS STYLING ==========
st.markdown("""
<style>
/* Main styling */
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.main .block-container {
    background-color: rgba(255, 255, 255, 0.98);
    border-radius: 15px;
    padding: 2.5rem;
    margin-top: 1rem;
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}

/* Headers */
.main-header {
    font-size: 3rem;
    color: #000000;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.sub-header {
    font-size: 1.8rem;
    color: #2c3e50;
    margin-bottom: 1.5rem;
    font-weight: 700;
    border-bottom: 3px solid #d4af37;
    padding-bottom: 0.5rem;
}

/* Sidebar */
section[data-testid="stSidebar"] > div {
    background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%) !important;
    border-right: 4px solid #d4af37;
    padding-top: 2rem !important;
}

/* Navigation buttons */
.sidebar-button {
    display: block;
    background: transparent;
    color: white !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    padding: 0.8rem 1rem !important;
    text-align: left;
    border-radius: 8px;
    transition: all 0.3s ease;
    cursor: pointer;
    margin: 5px 0;
    border: none;
    width: 100%;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.sidebar-button:hover {
    background: rgba(212, 175, 55, 0.2) !important;
    transform: translateX(5px);
    border-left: 3px solid #d4af37 !important;
}

.sidebar-button.active {
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%) !important;
    color: #000000 !important;
    font-weight: 700 !important;
}

/* Status popup */
.popup-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    padding: 18px 25px;
    border-radius: 12px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    z-index: 1000;
    animation: slideInRight 0.5s ease, fadeOut 0.5s ease 4.5s forwards;
    border-left: 5px solid #ffffff;
    max-width: 400px;
}

@keyframes slideInRight {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; transform: translateY(-20px); }
}

/* Example questions */
.example-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 15px;
    margin: 25px 0;
}

.example-btn {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border: 2px solid #d4af37;
    border-radius: 12px;
    padding: 18px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
    font-size: 1rem;
    font-weight: 500;
    color: #333;
    border: none;
    width: 100%;
}

.example-btn:hover {
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
    color: white;
    transform: translateY(-3px);
    box-shadow: 0 6px 15px rgba(212, 175, 55, 0.3);
}

/* Answer container */
.answer-container {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 12px;
    padding: 30px;
    margin: 25px 0;
    border-left: 6px solid #4a6491;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
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

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
    color: white !important;
    border: none !important;
    border-radius: 10px;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #b8860b 0%, #8b4513 100%);
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 15px rgba(0,0,0,0.2) !important;
}

/* Saved searches */
.saved-search-item {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    border-left: 4px solid #d4af37;
}

.saved-search-item:hover {
    background: rgba(255, 255, 255, 0.2);
}

.search-time {
    font-size: 0.8rem;
    color: #cccccc;
    margin-top: 5px;
}
</style>

<script>
// Auto-close popup after 5 seconds
setTimeout(function() {
    var popup = document.getElementById('documentsLoadedPopup');
    if (popup) {
        popup.style.animation = 'fadeOut 0.5s ease forwards';
        setTimeout(function() {
            if (popup.parentNode) {
                popup.parentNode.removeChild(popup);
            }
        }, 500);
    }
}, 5000);
</script>
""", unsafe_allow_html=True)

# ========== THREAD-SAFE DATABASE CONNECTION ==========

class ThreadSafeDatabase:
    """Thread-safe SQLite database connection for Streamlit"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.local = threading.local()
    
    def get_connection(self):
        """Get or create a thread-local database connection"""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
    
    def execute(self, query, params=None):
        """Execute a query and return cursor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

# ========== RESEARCH SYSTEM ==========

class ResearchSystem:
    """Research system for historical documents"""
    
    def __init__(self):
        # Set paths
        self.base_dir = Path(__file__).parent.parent
        self.db_path = self.base_dir / "data" / "knowledge_base.db"
        
        # Initialize components
        self.db = None
        self.documents_cache = []
        
        # Initialize analytics
        self.initialize_analytics()
        
        # Load everything
        self._initialize()
    
    def initialize_analytics(self):
        """Initialize analytics tracking"""
        if 'search_analytics' not in st.session_state:
            st.session_state.search_analytics = {
                'total_searches': 0,
                'searches_by_day': {},
                'searches_by_hour': {},
                'questions_asked': [],
                'response_times': [],
                'popular_topics': {},
                'user_sessions': []
            }
    
    def _initialize(self):
        """Initialize all components"""
        try:
            # 1. Check if files exist
            if not self.db_path.exists():
                print(f"Database not found: {self.db_path}")
                return False
            
            # 2. Initialize thread-safe database
            self.db = ThreadSafeDatabase(str(self.db_path))
            print(f"Database initialized: {self.db_path}")
            
            # 3. Test connection
            cursor = self.db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Found {len(tables)} tables")
            
            # 4. Load documents for cache
            self.documents_cache = self.get_all_documents(limit=1000)
            print(f"Documents cached: {len(self.documents_cache)} documents")
            
            return True
            
        except Exception as e:
            print(f"Initialization error: {str(e)}")
            return False
    
    def track_search(self, query, response_time, results_count):
        """Track search analytics"""
        analytics = st.session_state.search_analytics
        
        today = datetime.now().strftime("%Y-%m-%d")
        hour = datetime.now().strftime("%H:00")
        
        # Update counters
        analytics['total_searches'] += 1
        analytics['searches_by_day'][today] = analytics['searches_by_day'].get(today, 0) + 1
        analytics['searches_by_hour'][hour] = analytics['searches_by_hour'].get(hour, 0) + 1
        analytics['response_times'].append(response_time)
        
        # Track question
        analytics['questions_asked'].append({
            'question': query,
            'time': datetime.now().strftime("%H:%M:%S"),
            'results': results_count
        })
        
        # Track topic popularity
        words = query.lower().split()
        for word in words:
            if len(word) > 3 and word not in ['what', 'when', 'where', 'who', 'how', 'why']:
                analytics['popular_topics'][word] = analytics['popular_topics'].get(word, 0) + 1
        
        # Limit stored data
        if len(analytics['response_times']) > 1000:
            analytics['response_times'] = analytics['response_times'][-500:]
        if len(analytics['questions_asked']) > 100:
            analytics['questions_asked'] = analytics['questions_asked'][-50:]
    
    def get_database_stats(self):
        """Get database statistics"""
        if not self.db:
            return None
        
        try:
            cursor = self.db.execute("SELECT COUNT(*) FROM documents")
            total_docs = cursor.fetchone()[0]
            
            cursor = self.db.execute("SELECT source_type, COUNT(*) FROM documents GROUP BY source_type")
            docs_by_source = dict(cursor.fetchall())
            
            cursor = self.db.execute("SELECT COUNT(*) FROM entities")
            total_entities = cursor.fetchone()[0]
            
            cursor = self.db.execute("SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type")
            entities_by_type = dict(cursor.fetchall())
            
            # Get timeline events count
            cursor = self.db.execute("SELECT COUNT(*) FROM documents")
            timeline_events_approx = total_docs * 2
            
            # Get locations count
            cursor = self.db.execute("SELECT COUNT(DISTINCT entity_text) FROM entities WHERE entity_type = 'LOCATION'")
            geocoded_locations = cursor.fetchone()[0] or 25
            
            return {
                "total_documents": total_docs,
                "documents_by_source": docs_by_source,
                "total_entities": total_entities,
                "entities_by_type": entities_by_type,
                "timeline_events": timeline_events_approx,
                "geocoded_locations": geocoded_locations,
                "indexed_documents": len(self.documents_cache)
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return None
    
    def get_all_documents(self, limit=100, source_type=None):
        """Get all documents from database"""
        if not self.db:
            return []
        
        try:
            if source_type and source_type != "All":
                cursor = self.db.execute(
                    "SELECT * FROM documents WHERE source_type = ? ORDER BY id LIMIT ?",
                    (source_type, limit)
                )
            else:
                cursor = self.db.execute(
                    "SELECT * FROM documents ORDER BY id LIMIT ?",
                    (limit,)
                )
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting documents: {e}")
            return []
    
    def search_documents(self, query, limit=20):
        """Search documents using SQL LIKE"""
        if not self.db:
            return []
        
        try:
            search_pattern = f"%{query}%"
            cursor = self.db.execute(
                "SELECT * FROM documents WHERE title LIKE ? OR content LIKE ? OR author LIKE ? ORDER BY id LIMIT ?",
                (search_pattern, search_pattern, search_pattern, limit)
            )
            
            rows = cursor.fetchall()
            documents = [dict(row) for row in rows]
            
            # Add snippets
            for doc in documents:
                content = doc.get('content', '')
                if query.lower() in content.lower():
                    idx = content.lower().find(query.lower())
                    start = max(0, idx - 100)
                    end = min(len(content), idx + 200)
                    doc['snippet'] = content[start:end] + "..."
                else:
                    doc['snippet'] = content[:300] + "..."
            
            return documents
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def get_document_by_id(self, doc_id):
        """Get document by ID"""
        if not self.db:
            return None
        
        try:
            cursor = self.db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except:
            return None
    
    def get_entities(self, entity_type=None, limit=50):
        """Get entities from database"""
        if not self.db:
            return []
        
        try:
            if entity_type:
                cursor = self.db.execute(
                    "SELECT entity_text, entity_type, COUNT(*) as count FROM entities WHERE entity_type = ? GROUP BY entity_text ORDER BY count DESC LIMIT ?",
                    (entity_type, limit)
                )
            else:
                cursor = self.db.execute(
                    "SELECT entity_text, entity_type, COUNT(*) as count FROM entities GROUP BY entity_text, entity_type ORDER BY count DESC LIMIT ?",
                    (limit,)
                )
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except:
            return []
    
    def get_map_locations(self):
        """Get geographical locations for map"""
        locations_data = self.get_entities(entity_type='LOCATION', limit=50)
        
        # Coordinates for known locations
        location_coords = {
            'China': (35.8617, 104.1954),
            'Beijing': (39.9042, 116.4074),
            'Nanjing': (32.0603, 118.7969),
            'Shanghai': (31.2304, 121.4737),
            'India': (20.5937, 78.9629),
            'Sri Lanka': (7.8731, 80.7718),
            'Sumatra': (-0.5897, 101.3431),
            'Java': (-7.6145, 110.7123),
            'Africa': (8.7832, 34.5085),
            'America': (37.0902, -95.7129),
            'California': (36.7783, -119.4179),
            'Pacific Ocean': (0, -160),
            'Indian Ocean': (-20, 80),
            'South China Sea': (12, 115),
            'Malacca': (2.1896, 102.2501),
            'Calicut': (11.2588, 75.7804),
            'Hormuz': (27.1561, 56.2815),
            'Mombasa': (-4.0435, 39.6682),
            'Zanzibar': (-6.1659, 39.2026)
        }
        
        locations = []
        for entity in locations_data:
            loc_name = entity['entity_text']
            if loc_name in location_coords:
                lat, lon = location_coords[loc_name]
                locations.append({
                    'name': loc_name,
                    'latitude': lat,
                    'longitude': lon,
                    'type': 'city',
                    'mention_count': entity['count']
                })
        
        return {'locations': locations, 'total': len(locations)}
    
    def generate_answer(self, question, context_documents):
        """Generate an answer based on documents"""
        if not context_documents:
            return "I couldn't find specific information about that in the historical database. Try rephrasing your question or checking the example questions."
        
        # Combine document information
        document_summaries = []
        for doc in context_documents[:3]:
            summary = f"According to '{doc.get('title', 'Unknown')}' by {doc.get('author', 'Unknown')}: "
            content = doc.get('content', '')
            summary += content[:200] + "..." if len(content) > 200 else content
            document_summaries.append(summary)
        
        # Create a natural response
        responses = [
            f"Based on historical research, {question.lower().replace('?', '')} is addressed in several sources. ",
            f"Historical records indicate that {question.lower().replace('?', '')} ",
            f"Research on this topic shows that {question.lower().replace('?', '')} "
        ]
        
        base_response = random.choice(responses)
        
        # Add document insights
        if document_summaries:
            base_response += " ".join(document_summaries[:2])
            base_response += " This evidence comes from historical documents in the 1421 research database."
        
        return base_response

# ========== INITIALIZE SYSTEM ==========

@st.cache_resource
def init_system():
    """Initialize the research system"""
    system = ResearchSystem()
    return system

# ========== POPUP NOTIFICATION ==========

def show_popup_notification(message):
    """Show a popup notification"""
    st.markdown(f"""
    <div id="documentsLoadedPopup" class="popup-notification">
        <div style="font-size: 18px; font-weight: 600;">{message}</div>
    </div>
    """, unsafe_allow_html=True)

# ========== PAGE FUNCTIONS ==========

def show_dashboard(system):
    """Dashboard page"""
    st.markdown('<h2 class="sub-header">DASHBOARD</h2>', unsafe_allow_html=True)
    
    # Get stats
    stats = system.get_database_stats()
    
    if stats:
        # Display stats in columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", stats['total_documents'])
        with col2:
            st.metric("Historical Entities", stats['total_entities'])
        with col3:
            st.metric("Geocoded Locations", stats['geocoded_locations'])
        with col4:
            st.metric("Database Status", "Active")
    
    st.divider()
    
    # Ask Questions section
    st.markdown('<h2 class="sub-header">ASK HISTORICAL QUESTIONS</h2>', unsafe_allow_html=True)
    
    st.write("Enter a question about Chinese exploration, Zheng He's voyages, or the 1421 theory:")
    
    # Example questions
    st.write("**Example Questions:**")
    
    example_questions = [
        "What was Zheng He's most significant voyage?",
        "How does Gavin Menzies support his 1421 theory?",
        "What evidence exists for Chinese ships in America before Columbus?",
        "Describe Ming Dynasty naval technology and shipbuilding",
        "What were the main purposes of Chinese treasure fleets?",
        "How did Chinese navigation compare to European methods?",
        "What was the size of Zheng He's treasure ships?",
        "How did Chinese exploration influence world maps?",
        "What artifacts support pre-Columbian Chinese contact with America?",
        "How did the Ming Dynasty's policies change after Zheng He's voyages?"
    ]
    
    # Create grid of example questions
    cols = st.columns(2)
    for idx, question in enumerate(example_questions):
        with cols[idx % 2]:
            if st.button(
                f"{question}",
                key=f"example_{idx}",
                use_container_width=True
            ):
                st.session_state.current_question = question
                st.rerun()
    
    st.divider()
    
    # Question input
    # Initialize session state
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""
    
    question = st.text_area(
        "Your Question:",
        value=st.session_state.current_question,
        height=120,
        placeholder="Type your question here or click an example above...",
        key="question_input"
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        ask_btn = st.button("RESEARCH & ANSWER", type="primary", use_container_width=True)
    
    # Process question
    if ask_btn and question:
        start_time = time.time()
        with st.spinner("Researching historical records..."):
            # Search for relevant documents
            results = system.search_documents(question, limit=10)
            
            # Track search
            response_time = time.time() - start_time
            system.track_search(question, response_time, len(results))
            
            if results:
                # Generate answer
                answer = system.generate_answer(question, results)
                
                # Display answer
                st.markdown("""
                <div class="answer-container">
                """, unsafe_allow_html=True)
                
                st.markdown(f"**Answer:** {answer}")
                
                st.markdown("""
                </div>
                """, unsafe_allow_html=True)
                
                # Show sources
                with st.expander(f"SOURCES ({len(results)} documents found)", expanded=True):
                    st.write("**Relevant historical documents:**")
                    
                    for i, result in enumerate(results[:5]):
                        st.markdown(f"**{i+1}. {result['title']}**")
                        st.markdown(f"*Author: {result['author']}*")
                        st.markdown(f"*Type: {result['source_type']}*")
                        
                        if result.get('url'):
                            st.markdown(f"[View Source]({result['url']})")
                        
                        # Show relevance snippet
                        if result.get('snippet'):
                            st.markdown("**Relevant Excerpt:**")
                            st.info(result['snippet'])
                        
                        if i < len(results[:5]) - 1:
                            st.divider()
                
                # Save search
                if 'saved_searches' not in st.session_state:
                    st.session_state.saved_searches = []
                
                save_search = st.checkbox("Save this search")
                if save_search:
                    search_entry = {
                        'id': len(st.session_state.saved_searches) + 1,
                        'query': question,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'results': len(results),
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'time': datetime.now().strftime("%H:%M")
                    }
                    st.session_state.saved_searches.append(search_entry)
                    st.success(f"Search saved! Total saved searches: {len(st.session_state.saved_searches)}")
                
            else:
                st.warning("""
                **No specific documents found** for your question.
                
                Try:
                - Using different keywords
                - Asking more general questions about Chinese exploration
                - Referring to the example questions above
                """)

def show_documents_page(system):
    """Research Documents page"""
    st.markdown('<h2 class="sub-header">RESEARCH DOCUMENTS</h2>', unsafe_allow_html=True)
    
    # Search controls
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input("Search documents:", placeholder="Title, author, or keywords...", label_visibility="collapsed")
    with col2:
        source_filter = st.selectbox(
            "Filter by type",
            ["All", "Book", "Article", "Research Paper", "Website"],
            index=0
        )
    with col3:
        limit = st.selectbox("Results", [25, 50, 100], index=0)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        search_clicked = st.button("SEARCH DOCUMENTS", type="primary", use_container_width=True)
    with col2:
        show_all_clicked = st.button("SHOW ALL DOCUMENTS", use_container_width=True)
    
    # Load documents
    documents = []
    if search_clicked and search_query:
        start_time = time.time()
        with st.spinner("Searching documents..."):
            documents = system.search_documents(search_query, limit=limit)
            response_time = time.time() - start_time
            system.track_search(search_query, response_time, len(documents))
            if documents:
                st.success(f"Found {len(documents)} documents")
    elif show_all_clicked:
        with st.spinner("Loading all documents..."):
            documents = system.get_all_documents(limit=limit, source_type=source_filter)
            if documents:
                st.success(f"Loaded {len(documents)} documents")
    
    # Display results
    if documents:
        # Create table data
        table_data = []
        for doc in documents:
            doc_id = doc.get('id') or ''
            table_data.append({
                'ID': doc_id,
                'Title': doc.get('title', 'Untitled'),
                'Author': doc.get('author', 'Unknown'),
                'Type': doc.get('source_type', 'Unknown'),
                'Words': doc.get('word_count', 0),
                'URL': doc.get('url', '')[:40] + "..." if len(doc.get('url', '')) > 40 else doc.get('url', '')
            })
        
        df = pd.DataFrame(table_data)
        
        # Display table
        st.dataframe(
            df,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Title": st.column_config.TextColumn("Document Title", width="large"),
                "Author": st.column_config.TextColumn("Author", width="medium"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Words": st.column_config.NumberColumn("Words", width="small"),
                "URL": st.column_config.TextColumn("URL", width="medium")
            },
            use_container_width=True,
            height=500,
            hide_index=True
        )
        
        # Export option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "DOWNLOAD AS CSV",
            data=csv,
            file_name=f"documents_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    elif search_clicked or show_all_clicked:
        st.info("No documents found. Try different search terms or filters.")

def show_map_page(system):
    """Full Voyage Map page"""
    st.markdown('<h2 class="sub-header">FULL VOYAGE MAP</h2>', unsafe_allow_html=True)
    
    st.write("Explore geographical locations mentioned in historical documents about Chinese exploration.")
    
    with st.spinner("Loading geographical data..."):
        map_data = system.get_map_locations()
        
        if map_data and map_data['locations']:
            locations = map_data['locations']
            
            # Create map
            fig = go.Figure()
            
            lats = [loc['latitude'] for loc in locations]
            lons = [loc['longitude'] for loc in locations]
            names = [loc['name'] for loc in locations]
            counts = [loc['mention_count'] for loc in locations]
            
            fig.add_trace(go.Scattergeo(
                lon=lons,
                lat=lats,
                mode='markers+text',
                marker=dict(
                    size=[min(c * 3, 25) for c in counts],
                    color='#FF5722',
                    line=dict(width=2, color='white')
                ),
                text=names,
                textposition="top center",
                name='Historical Locations',
                hovertemplate='<b>%{text}</b><br>Mentions: %{marker.size}<extra></extra>'
            ))
            
            # Add voyage routes
            if len(lats) > 2:
                fig.add_trace(go.Scattergeo(
                    lon=lons[:5],
                    lat=lats[:5],
                    mode='lines',
                    line=dict(width=2, color='#d4af37', dash='dash'),
                    name='Possible Voyage Route'
                ))
            
            fig.update_layout(
                title="Chinese Exploration Voyage Map",
                geo=dict(
                    showland=True,
                    landcolor='rgb(243, 243, 243)',
                    coastlinecolor='rgb(204, 204, 204)',
                    showcountries=True,
                    countrycolor='rgb(204, 204, 204)',
                    showocean=True,
                    oceancolor='rgb(230, 245, 255)',
                    projection_type='natural earth',
                    showlakes=True,
                    lakecolor='rgb(230, 245, 255)'
                ),
                height=600,
                showlegend=True,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Location table
            with st.expander("LOCATION DETAILS", expanded=False):
                loc_df = pd.DataFrame(locations)
                st.dataframe(
                    loc_df[['name', 'type', 'mention_count']].sort_values('mention_count', ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No geographical location data available in the database.")

def show_analytics_page(system):
    """Analytics page"""
    st.markdown('<h2 class="sub-header">ANALYTICS DASHBOARD</h2>', unsafe_allow_html=True)
    
    analytics = st.session_state.search_analytics
    stats = system.get_database_stats()
    
    if stats:
        # Key Metrics
        st.subheader("Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Searches", analytics['total_searches'])
        with col2:
            avg_time = sum(analytics['response_times']) / max(1, len(analytics['response_times']))
            st.metric("Avg Response Time", f"{avg_time:.2f}s")
        with col3:
            unique_days = len(analytics['searches_by_day'])
            st.metric("Active Days", unique_days)
        with col4:
            topics = len(analytics['popular_topics'])
            st.metric("Topics Tracked", topics)
        
        st.divider()
        
        # Search Activity
        st.subheader("Search Activity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Searches by Day
            if analytics['searches_by_day']:
                days = list(analytics['searches_by_day'].keys())[-10:]
                counts = [analytics['searches_by_day'][d] for d in days]
                
                fig = go.Figure(data=[
                    go.Bar(x=days, y=counts, marker_color='#4a6491')
                ])
                fig.update_layout(
                    title="Searches by Day (Last 10 Days)",
                    xaxis_title="Date",
                    yaxis_title="Number of Searches",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Response Time Distribution
            if analytics['response_times']:
                fig = go.Figure(data=[
                    go.Histogram(
                        x=analytics['response_times'],
                        nbinsx=20,
                        marker_color='#28a745'
                    )
                ])
                fig.update_layout(
                    title="Response Time Distribution",
                    xaxis_title="Response Time (seconds)",
                    yaxis_title="Frequency",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Top Topics
        st.subheader("Top Search Topics")
        if analytics['popular_topics']:
            topics_df = pd.DataFrame(
                list(analytics['popular_topics'].items()),
                columns=['Topic', 'Count']
            )
            topics_df = topics_df.sort_values('Count', ascending=False).head(10)
            
            fig = px.bar(
                topics_df,
                x='Count',
                y='Topic',
                orientation='h',
                title="Most Popular Topics",
                color='Count',
                color_continuous_scale='Oranges'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Database Statistics
        st.divider()
        st.subheader("Database Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Document Types:**")
            for source_type, count in stats['documents_by_source'].items():
                st.write(f"- {source_type}: {count}")
        
        with col2:
            st.write("**Entity Types:**")
            for entity_type, count in stats['entities_by_type'].items():
                st.write(f"- {entity_type}: {count}")
        
        # Recent Searches
        if analytics['questions_asked']:
            st.divider()
            st.subheader("Recent Searches")
            
            recent_df = pd.DataFrame(analytics['questions_asked'][-10:])
            st.dataframe(recent_df, use_container_width=True, hide_index=True)
    
    else:
        st.info("No analytics data available yet. Start searching to generate analytics.")

def show_saved_searches_page():
    """Saved Searches page"""
    st.markdown('<h2 class="sub-header">SAVED SEARCHES</h2>', unsafe_allow_html=True)
    
    if 'saved_searches' not in st.session_state:
        st.session_state.saved_searches = []
    
    if st.session_state.saved_searches:
        st.write(f"**Total Saved Searches:** {len(st.session_state.saved_searches)}")
        
        for i, search in enumerate(st.session_state.saved_searches):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"""
                <div class="saved-search-item">
                    <strong>{search['query'][:50]}{'...' if len(search['query']) > 50 else ''}</strong>
                    <div class="search-time">
                        Saved: {search['timestamp']} | Results: {search['results']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("SEARCH AGAIN", key=f"again_{search['id']}", use_container_width=True):
                    st.session_state.current_question = search['query']
                    st.session_state.current_page = "dashboard"
                    st.rerun()
            
            with col3:
                if st.button("DELETE", key=f"delete_{search['id']}", type="secondary", use_container_width=True):
                    st.session_state.saved_searches = [s for s in st.session_state.saved_searches if s['id'] != search['id']]
                    st.success("Search deleted!")
                    st.rerun()
        
        # Clear all button
        if st.button("CLEAR ALL SAVED SEARCHES", type="secondary", use_container_width=True):
            st.session_state.saved_searches = []
            st.success("All saved searches cleared!")
            st.rerun()
    else:
        st.info("No saved searches yet. Save searches from the Dashboard to see them here.")

def show_settings_page(system):
    """Settings page"""
    st.markdown('<h2 class="sub-header">SYSTEM SETTINGS</h2>', unsafe_allow_html=True)
    
    # System info
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Database Information")
        stats = system.get_database_stats()
        if stats:
            st.write(f"**Total Documents:** {stats['total_documents']}")
            st.write(f"**Historical Entities:** {stats['total_entities']}")
            st.write(f"**Document Sources:** {len(stats['documents_by_source'])}")
            st.write(f"**Geocoded Locations:** {stats['geocoded_locations']}")
    
    with col2:
        st.subheader("System Status")
        st.write(f"**Database Path:** `{system.db_path}`")
        st.write(f"**Database Connection:** {'Active' if system.db else 'Inactive'}")
        st.write(f"**Cached Documents:** {len(system.documents_cache)}")
    
    st.divider()
    
    # Actions
    st.subheader("Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("REFRESH CACHE", use_container_width=True):
            st.cache_resource.clear()
            st.success("System cache cleared!")
            st.rerun()
    
    with col2:
        if st.button("CHECK DATABASE", use_container_width=True):
            if system.db:
                try:
                    cursor = system.db.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    st.success(f"Database connection OK. Found {len(tables)} tables.")
                except Exception as e:
                    st.error(f"Database error: {str(e)}")
            else:
                st.error("Database not initialized")
    
    # Reset analytics
    st.divider()
    st.subheader("Analytics Management")
    
    if st.button("RESET ANALYTICS DATA", type="secondary", use_container_width=True):
        st.session_state.search_analytics = {
            'total_searches': 0,
            'searches_by_day': {},
            'searches_by_hour': {},
            'questions_asked': [],
            'response_times': [],
            'popular_topics': {},
            'user_sessions': []
        }
        st.success("Analytics data reset!")

# ========== CUSTOM SIDEBAR ==========

def render_sidebar():
    """Render custom sidebar with clickable navigation"""
    with st.sidebar:
        # Logo/Title
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #d4af37; font-size: 1.8rem; font-weight: 800;">1421 AI</h2>
            <p style="color: #ffffff; opacity: 0.8; font-size: 1rem;">HISTORICAL RESEARCH SYSTEM</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        pages = [
            ("DASHBOARD", "dashboard"),
            ("RESEARCH DOCUMENTS", "documents"),
            ("FULL VOYAGE MAP", "map"),
            ("ANALYTICS", "analytics"),
            ("SAVED SEARCHES", "saved_searches"),
            ("SETTINGS", "settings")
        ]
        
        current_page = st.session_state.get('current_page', 'dashboard')
        
        for label, page_id in pages:
            if st.button(
                label,
                key=f"nav_{page_id}",
                use_container_width=True,
                type="primary" if current_page == page_id else "secondary"
            ):
                st.session_state.current_page = page_id
                st.rerun()
        
        st.divider()
        
        # Quick stats
        if 'system_stats' in st.session_state:
            stats = st.session_state.system_stats
            st.markdown("""
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 20px;">
                <h4 style="color: #d4af37; margin-bottom: 10px; font-size: 1rem;">SYSTEM STATUS</h4>
                <p style="color: white; margin: 5px 0; font-size: 0.9rem;"><strong>Documents:</strong> {}</p>
                <p style="color: white; margin: 5px 0; font-size: 0.9rem;"><strong>Locations:</strong> {}</p>
                <p style="color: white; margin: 5px 0; font-size: 0.9rem;"><strong>Entities:</strong> {}</p>
            </div>
            """.format(
                stats.get('total_documents', 0) if stats else 0,
                stats.get('geocoded_locations', 25) if stats else 25,
                stats.get('total_entities', 0) if stats else 0
            ), unsafe_allow_html=True)

# ========== MAIN APPLICATION ==========

def main():
    """Main application"""
    
    # Custom HTML for header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h1 class="main-header">1421 AI - HISTORICAL RESEARCH SYSTEM</h1>
        <p style="font-size: 1.2rem; color: #666; max-width: 800px; margin: 0 auto;">
            A comprehensive research platform for studying Chinese exploration history and the 1421 theory
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize system
    with st.spinner("Initializing research system..."):
        system = init_system()
    
    if system is None or not system.db:
        st.error("""
        ## SYSTEM INITIALIZATION FAILED
        
        **Troubleshooting Steps:**
        1. Make sure `knowledge_base.db` is in the `data/` folder
        2. Check the file is properly uploaded to GitHub
        3. Verify database is not corrupted
        """)
        
        base_dir = Path(__file__).parent.parent
        db_path = base_dir / "data" / "knowledge_base.db"
        
        st.write(f"- Database path: `{db_path}`")
        st.write(f"- Database exists: `{db_path.exists()}`")
        
        st.stop()
    
    # Get and store stats
    stats = system.get_database_stats()
    if stats:
        st.session_state.system_stats = stats
        
        # Show popup notification
        if stats['total_documents'] > 0:
            show_popup_notification(f"System Status: {stats['total_documents']} historical documents loaded and ready for research")
    
    # Render sidebar
    render_sidebar()
    
    # Set default page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    # Main content area
    current_page = st.session_state.get('current_page', 'dashboard')
    
    # Show selected page
    if current_page == "dashboard":
        show_dashboard(system)
    elif current_page == "documents":
        show_documents_page(system)
    elif current_page == "map":
        show_map_page(system)
    elif current_page == "analytics":
        show_analytics_page(system)
    elif current_page == "saved_searches":
        show_saved_searches_page()
    elif current_page == "settings":
        show_settings_page(system)

if __name__ == "__main__":
    main()
