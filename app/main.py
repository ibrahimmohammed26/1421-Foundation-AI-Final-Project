"""
1421 Historical Research System - Final Working Version
Simplified for Streamlit Cloud Compatibility
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
import sys
import os

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="1421 Historical Research System",
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

/* Sidebar */
section[data-testid="stSidebar"] > div {
    background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%) !important;
    border-right: 4px solid #d4af37;
    padding-top: 2rem !important;
}

/* Navigation links */
.nav-link {
    display: block;
    background: transparent;
    color: white !important;
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    padding: 0.8rem 1rem !important;
    text-align: left;
    border-radius: 8px;
    transition: all 0.3s ease;
    cursor: pointer;
    margin: 5px 0;
    border: none;
    width: 100%;
}

.nav-link:hover {
    background: rgba(212, 175, 55, 0.2) !important;
    transform: translateX(5px);
    border-left: 3px solid #d4af37 !important;
}

.nav-link.active {
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
    animation: slideInRight 0.5s ease;
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

/* Question examples */
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
    padding: 20px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
    font-size: 1.1rem;
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

/* Section headers */
.section-header {
    font-size: 2.2rem !important;
    color: #2c3e50;
    margin-bottom: 1.5rem !important;
    font-weight: 700;
    border-bottom: 3px solid #d4af37;
    padding-bottom: 0.5rem;
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
        
        # Load everything
        self._initialize()
    
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
            
            return {
                "total_documents": total_docs,
                "documents_by_source": docs_by_source,
                "total_entities": total_entities,
                "entities_by_type": entities_by_type,
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
    st.markdown('<h2 class="section-header">📊 Dashboard</h2>', unsafe_allow_html=True)
    
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
            st.metric("Document Sources", len(stats['documents_by_source']))
        with col4:
            st.metric("Database Status", "✅ Active")
        
        # Show popup notification for document count
        if stats['total_documents'] > 0:
            show_popup_notification(f"✅ System Ready: {stats['total_documents']} documents loaded")
    
    st.divider()
    
    # Quick search
    st.subheader("🔍 Quick Document Search")
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search the database:", placeholder="Enter keywords, titles, or authors...", label_visibility="collapsed")
    with col2:
        search_btn = st.button("Search", type="primary", use_container_width=True)
    
    if search_btn and query:
        with st.spinner("Searching historical documents..."):
            results = system.search_documents(query, limit=15)
            
            if results:
                st.success(f"📚 Found {len(results)} documents")
                
                for i, result in enumerate(results[:5]):
                    with st.expander(f"**{i+1}. {result['title']}**", expanded=(i==0)):
                        st.write(f"**Author:** {result['author']}")
                        st.write(f"**Source Type:** {result['source_type']}")
                        if result.get('url'):
                            st.markdown(f"**Source:** [{result['url'][:50]}...]({result['url']})")
                        st.divider()
                        st.write("**Excerpt:**")
                        st.write(result.get('snippet', 'No content available'))
            else:
                st.info("No documents found. Try different keywords.")

def show_ask_question(system):
    """Ask Question section"""
    st.markdown('<h2 class="section-header">🤔 Ask Historical Questions</h2>', unsafe_allow_html=True)
    
    st.write("""
    Ask questions about Chinese exploration, Zheng He's voyages, Ming Dynasty history, 
    or any topic related to the 1421 theory.
    """)
    
    # Example questions
    st.subheader("💡 Try These Questions:")
    
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
                f"❓ {question}",
                key=f"example_{idx}",
                use_container_width=True
            ):
                st.session_state.current_question = question
                st.session_state.auto_submit = True
                st.rerun()
    
    st.divider()
    
    # Question input
    st.subheader("📝 Your Question")
    
    # Initialize session state
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""
    if 'auto_submit' not in st.session_state:
        st.session_state.auto_submit = False
    
    question = st.text_area(
        "Enter your historical question:",
        value=st.session_state.current_question,
        height=120,
        placeholder="Type your question here or click an example above...",
        key="question_input"
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        ask_btn = st.button("🔍 Research & Answer", type="primary", use_container_width=True)
    
    # Handle auto-submit
    if st.session_state.auto_submit:
        ask_btn = True
        question = st.session_state.current_question
        st.session_state.auto_submit = False
    
    # Process question
    if ask_btn and question:
        with st.spinner("🔍 Researching historical records..."):
            # Search for relevant documents
            results = system.search_documents(question, limit=10)
            
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
                with st.expander(f"📚 Sources ({len(results)} documents found)", expanded=True):
                    st.write("**Relevant historical documents:**")
                    
                    for i, result in enumerate(results[:5]):
                        st.markdown(f"**{i+1}. {result['title']}**")
                        st.markdown(f"*Author: {result['author']}*")
                        st.markdown(f"*Type: {result['source_type']}*")
                        
                        if result.get('url'):
                            st.markdown(f"[🔗 View Source]({result['url']})")
                        
                        # Show relevance snippet
                        if result.get('snippet'):
                            st.markdown("**Relevant Excerpt:**")
                            st.info(result['snippet'])
                        
                        if i < len(results[:5]) - 1:
                            st.divider()
                
            else:
                st.warning("""
                ⚠️ **No specific documents found** for your question.
                
                Try:
                - Using different keywords
                - Asking more general questions about Chinese exploration
                - Referring to the example questions above
                """)

def show_documents_page(system):
    """Research Documents page"""
    st.markdown('<h2 class="section-header">📄 Research Documents</h2>', unsafe_allow_html=True)
    
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
        search_clicked = st.button("🔍 Search Documents", type="primary", use_container_width=True)
    with col2:
        show_all_clicked = st.button("📋 Show All Documents", use_container_width=True)
    
    # Load documents
    documents = []
    if search_clicked and search_query:
        with st.spinner("Searching documents..."):
            documents = system.search_documents(search_query, limit=limit)
            if documents:
                st.success(f"✅ Found {len(documents)} documents")
    elif show_all_clicked:
        with st.spinner("Loading all documents..."):
            documents = system.get_all_documents(limit=limit, source_type=source_filter)
            if documents:
                st.success(f"✅ Loaded {len(documents)} documents")
    
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
            "📥 Download as CSV",
            data=csv,
            file_name=f"documents_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    elif search_clicked or show_all_clicked:
        st.info("No documents found. Try different search terms or filters.")

def show_map_page(system):
    """Voyage Map page"""
    st.markdown('<h2 class="section-header">🗺️ Voyage Map</h2>', unsafe_allow_html=True)
    
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
            with st.expander("📍 Location Details", expanded=False):
                loc_df = pd.DataFrame(locations)
                st.dataframe(
                    loc_df[['name', 'type', 'mention_count']].sort_values('mention_count', ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No geographical location data available in the database.")

def show_settings_page(system):
    """Settings page"""
    st.markdown('<h2 class="section-header">⚙️ System Settings</h2>', unsafe_allow_html=True)
    
    # System info
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Database Information")
        stats = system.get_database_stats()
        if stats:
            st.write(f"**Total Documents:** {stats['total_documents']}")
            st.write(f"**Historical Entities:** {stats['total_entities']}")
            st.write(f"**Document Sources:** {len(stats['documents_by_source'])}")
            
            if stats['documents_by_source']:
                st.write("**Documents by Type:**")
                for source_type, count in stats['documents_by_source'].items():
                    st.write(f"  - {source_type}: {count}")
    
    with col2:
        st.subheader("System Status")
        st.write(f"**Database Path:** `{system.db_path}`")
        st.write(f"**Database Connection:** {'✅ Active' if system.db else '❌ Inactive'}")
        st.write(f"**Cached Documents:** {len(system.documents_cache)}")
    
    st.divider()
    
    # Actions
    st.subheader("Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Cache", use_container_width=True):
            st.cache_resource.clear()
            st.success("System cache cleared!")
            st.rerun()
    
    with col2:
        if st.button("📊 Check Database", use_container_width=True):
            if system.db:
                try:
                    cursor = system.db.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    st.success(f"Database connection OK. Found {len(tables)} tables.")
                except Exception as e:
                    st.error(f"Database error: {str(e)}")
            else:
                st.error("Database not initialized")

# ========== CUSTOM SIDEBAR ==========

def render_sidebar():
    """Render custom sidebar with clickable navigation"""
    with st.sidebar:
        # Logo/Title
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #d4af37; font-size: 1.8rem;">1421 Research</h2>
            <p style="color: #ffffff; opacity: 0.8;">Historical Exploration System</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        pages = [
            ("📊 Dashboard", "dashboard"),
            ("📄 Research Documents", "documents"),
            ("🗺️ Voyage Map", "map"),
            ("⚙️ Settings", "settings")
        ]
        
        current_page = st.session_state.get('current_page', 'dashboard')
        
        for label, page_id in pages:
            if st.button(
                label,
                key=f"nav_{page_id}",
                use_container_width=True
            ):
                st.session_state.current_page = page_id
                st.rerun()
        
        st.divider()
        
        # Quick stats
        if 'system_stats' in st.session_state:
            stats = st.session_state.system_stats
            st.markdown("""
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 20px;">
                <h4 style="color: #d4af37; margin-bottom: 10px;">Quick Stats</h4>
                <p style="color: white; margin: 5px 0;">📚 <strong>Documents:</strong> {}</p>
                <p style="color: white; margin: 5px 0;">📍 <strong>Locations:</strong> 25+</p>
                <p style="color: white; margin: 5px 0;">⚓ <strong>Voyages:</strong> 3</p>
            </div>
            """.format(stats.get('total_documents', 0) if stats else 0), unsafe_allow_html=True)

# ========== MAIN APPLICATION ==========

def main():
    """Main application"""
    
    # Custom HTML for header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h1 class="main-header">1421 Historical Research System</h1>
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
        ## System Initialization Failed
        
        **Troubleshooting Steps:**
        1. Make sure `knowledge_base.db` is in the `data/` folder
        2. Check the file is properly uploaded to GitHub
        3. Verify database is not corrupted
        
        **File Check Results:**
        """)
        
        base_dir = Path(__file__).parent.parent
        db_path = base_dir / "data" / "knowledge_base.db"
        
        st.write(f"- Database path: `{db_path}`")
        st.write(f"- Database exists: `{db_path.exists()}`")
        
        if db_path.exists():
            file_size = db_path.stat().st_size / (1024*1024)
            st.write(f"- File size: `{file_size:.2f} MB`")
        
        st.stop()
    
    # Get and store stats
    stats = system.get_database_stats()
    if stats:
        st.session_state.system_stats = stats
        
        # Show status
        if stats['total_documents'] > 0:
            show_popup_notification(f"✅ System Ready: {stats['total_documents']} documents loaded")
    
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
        st.divider()
        show_ask_question(system)
    elif current_page == "documents":
        show_documents_page(system)
    elif current_page == "map":
        show_map_page(system)
    elif current_page == "settings":
        show_settings_page(system)

if __name__ == "__main__":
    main()
