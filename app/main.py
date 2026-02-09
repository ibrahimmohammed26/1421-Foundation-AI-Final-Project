"""
1421 Historical Research System - Main Application
FIXED VERSION: Thread-safe SQLite for Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import faiss
import pickle
import json
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import sys
import os
import threading

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
    background-color: rgba(255, 255, 255, 0.95);
    border-radius: 10px;
    padding: 2rem;
    margin-top: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Headers */
.main-header {
    font-size: 2.5rem;
    color: #000000;
    text-align: center;
    margin-bottom: 1.5rem;
    font-weight: 700;
}

/* Sidebar */
section[data-testid="stSidebar"] > div {
    background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%) !important;
    border-right: 3px solid #d4af37;
    padding-top: 1rem !important;
}

section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%) !important;
    color: #000000 !important;
    border: 2px solid #ffffff !important;
    border-radius: 6px;
    font-weight: 600 !important;
    margin: 3px 0 !important;
    padding: 0.4rem 0.8rem !important;
    width: 100%;
}

/* Status badges */
.status-badge {
    display: inline-block;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 16px;
    margin: 10px 0;
    text-align: center;
}

.status-loaded {
    background: #28a745;
    color: white;
}

.status-error {
    background: #dc3545;
    color: white;
}

/* Answer container */
.answer-container {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 8px;
    padding: 20px;
    margin: 15px 0;
    border-left: 4px solid #4a6491;
}

/* Metrics */
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700;
}

[data-testid="stMetricLabel"] {
    font-weight: 600;
    font-size: 0.9rem !important;
}
</style>
""", unsafe_allow_html=True)

# ========== THREAD-SAFE DATABASE CONNECTION ==========

class ThreadSafeDatabase:
    """Thread-safe SQLite database connection"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.local = threading.local()
    
    def get_connection(self):
        """Get or create a thread-local database connection"""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
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
    
    def close(self):
        """Close all connections"""
        if hasattr(self.local, 'conn'):
            self.local.conn.close()
            del self.local.conn

# ========== UNIFIED RESEARCH SYSTEM ==========

class ResearchSystem:
    """Complete research system - thread-safe for Streamlit Cloud"""
    
    def __init__(self):
        # Set paths
        self.base_dir = Path(__file__).parent.parent
        self.db_path = self.base_dir / "data" / "knowledge_base.db"
        self.vector_dir = self.base_dir / "data" / "vector_databases" / "main_index"
        
        # Initialize components
        self.db = None
        self.index = None
        self.documents = []
        self.metadatas = []
        self.model = None
        
        # Load everything
        self._initialize()
    
    def _initialize(self):
        """Initialize all components"""
        try:
            # 1. Check if files exist
            if not self.db_path.exists():
                print(f"❌ Database not found: {self.db_path}")
                return False
            
            # 2. Initialize thread-safe database
            self.db = ThreadSafeDatabase(str(self.db_path))
            print(f"✅ Database initialized: {self.db_path}")
            
            # 3. Vector database
            index_file = self.vector_dir / "faiss_index.bin"
            metadata_file = self.vector_dir / "faiss_metadata.pkl"
            
            if index_file.exists() and metadata_file.exists():
                self.index = faiss.read_index(str(index_file))
                with open(metadata_file, 'rb') as f:
                    metadata = pickle.load(f)
                    self.documents = metadata.get('documents', [])
                    self.metadatas = metadata.get('metadatas', [])
                print(f"✅ Vector database loaded: {len(self.documents)} documents")
            else:
                print(f"⚠️ Vector database not found: {self.vector_dir}")
            
            # 4. Embedding model
            @st.cache_resource
            def load_embedding_model():
                return SentenceTransformer('all-MiniLM-L6-v2')
            
            self.model = load_embedding_model()
            print("✅ Embedding model loaded")
            
            return True
            
        except Exception as e:
            print(f"❌ Initialization error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def get_database_stats(self):
        """Get database statistics - THREAD-SAFE"""
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
                "vector_documents": len(self.documents)
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def get_all_documents(self, limit=100, source_type=None):
        """Get all documents from database - THREAD-SAFE"""
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
        """Search documents using SQL LIKE - THREAD-SAFE"""
        if not self.db:
            return []
        
        try:
            search_pattern = f"%{query}%"
            cursor = self.db.execute(
                "SELECT * FROM documents WHERE title LIKE ? OR content LIKE ? OR author LIKE ? ORDER BY id LIMIT ?",
                (search_pattern, search_pattern, search_pattern, limit)
            )
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def semantic_search(self, query, k=10):
        """Semantic search using vector database"""
        if not self.index or not self.model:
            return []
        
        try:
            query_embedding = self.model.encode([query]).astype('float32')
            distances, indices = self.index.search(query_embedding, k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.metadatas):
                    doc_id = self.metadatas[idx]['id']
                    doc = self.get_document_by_id(doc_id)
                    if doc:
                        results.append({
                            'document_id': doc_id,
                            'title': doc.get('title', 'Untitled'),
                            'author': doc.get('author', 'Unknown'),
                            'source_type': doc.get('source_type', 'Unknown'),
                            'url': doc.get('url', ''),
                            'word_count': doc.get('word_count', 0),
                            'snippet': doc.get('content', '')[:300] + "...",
                            'similarity': float(1.0 / (1.0 + distances[0][i]))
                        })
            return results
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
    
    def get_document_by_id(self, doc_id):
        """Get document by ID - THREAD-SAFE"""
        if not self.db:
            return None
        
        try:
            cursor = self.db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except:
            return None
    
    def get_entities(self, entity_type=None, limit=50):
        """Get entities from database - THREAD-SAFE"""
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

# ========== INITIALIZE SYSTEM ==========

@st.cache_resource
def init_system():
    """Initialize the research system"""
    system = ResearchSystem()
    
    # Check if files exist
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "knowledge_base.db"
    vector_dir = base_dir / "data" / "vector_databases" / "main_index"
    
    if not db_path.exists():
        st.error(f"❌ Database file not found: {db_path}")
        return None
    
    # Test database connection
    try:
        test_conn = sqlite3.connect(str(db_path), check_same_thread=False)
        cursor = test_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        test_conn.close()
        
        if table_count == 0:
            st.error("❌ Database exists but has no tables")
            return None
            
    except Exception as e:
        st.error(f"❌ Cannot open database: {str(e)}")
        return None
    
    return system

# ========== PAGE FUNCTIONS ==========

def show_dashboard(system):
    """Dashboard page"""
    st.header("Dashboard")
    
    # Get stats
    stats = system.get_database_stats()
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", stats['total_documents'])
        with col2:
            st.metric("Total Entities", stats['total_entities'])
        with col3:
            st.metric("Vector Docs", stats['vector_documents'])
        with col4:
            st.metric("Sources", len(stats['documents_by_source']))
    
    st.divider()
    
    # Quick search
    st.subheader("Quick Search")
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search the database:", placeholder="Enter keywords...")
    with col2:
        search_btn = st.button("Search", use_container_width=True)
    
    if search_btn and query:
        with st.spinner("Searching..."):
            results = system.semantic_search(query, k=10)
            
            if results:
                st.success(f"Found {len(results)} documents")
                
                for i, result in enumerate(results[:5]):
                    with st.expander(f"{i+1}. {result['title']}"):
                        st.write(f"**Author:** {result['author']}")
                        st.write(f"**Type:** {result['source_type']}")
                        st.write(f"**Relevance:** {result['similarity']:.1%}")
                        st.write(result['snippet'])
                        if result['url']:
                            st.markdown(f"[View Source]({result['url']})")
            else:
                st.info("No results found. Trying keyword search...")
                sql_results = system.search_documents(query)
                if sql_results:
                    st.success(f"Found {len(sql_results)} documents using keyword search")
                else:
                    st.warning("No documents found")

def show_documents_page(system):
    """Research Documents page"""
    st.header("Research Documents")
    
    # Search controls
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input("Search documents:", placeholder="Title, author, or keywords")
    with col2:
        source_filter = st.selectbox(
            "Document type",
            ["All", "Book", "Article", "Research Paper", "Website"],
            index=0
        )
    with col3:
        limit = st.selectbox("Results", [25, 50, 100], index=0)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        search_clicked = st.button("Search Documents", type="primary", use_container_width=True)
    with col2:
        show_all_clicked = st.button("Show All Documents", use_container_width=True)
    
    # Load documents
    documents = []
    if search_clicked and search_query:
        with st.spinner("Searching..."):
            documents = system.semantic_search(search_query, k=limit)
            if not documents:
                documents = system.search_documents(search_query, limit=limit)
    elif show_all_clicked:
        with st.spinner("Loading all documents..."):
            documents = system.get_all_documents(limit=limit, source_type=source_filter)
    
    # Display results
    if documents:
        st.success(f"Loaded {len(documents)} documents")
        
        # Create table data
        table_data = []
        for doc in documents:
            doc_id = doc.get('id') or doc.get('document_id') or ''
            table_data.append({
                'ID': doc_id,
                'Title': doc.get('title', 'Untitled'),
                'Author': doc.get('author', 'Unknown'),
                'Type': doc.get('source_type', 'Unknown'),
                'Words': doc.get('word_count', 0),
                'URL': doc.get('url', '')[:50] + "..." if len(doc.get('url', '')) > 50 else doc.get('url', '')
            })
        
        df = pd.DataFrame(table_data)
        
        # Display table
        st.dataframe(
            df,
            column_config={
                "ID": st.column_config.NumberColumn(width="small"),
                "Title": st.column_config.TextColumn(width="large"),
                "Author": st.column_config.TextColumn(width="medium"),
                "Type": st.column_config.TextColumn(width="small"),
                "Words": st.column_config.NumberColumn(width="small"),
                "URL": st.column_config.TextColumn(width="medium")
            },
            use_container_width=True,
            height=500,
            hide_index=True
        )
        
        # Export option
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download as CSV",
            data=csv,
            file_name=f"documents_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Use the buttons above to load documents")

def show_map_page(system):
    """Voyage Map page"""
    st.header("Voyage Map")
    
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
                name='Historical Locations'
            ))
            
            fig.update_layout(
                title="Historical Voyage Locations",
                geo=dict(
                    showland=True,
                    landcolor='rgb(243, 243, 243)',
                    coastlinecolor='rgb(204, 204, 204)',
                    showcountries=True,
                    countrycolor='rgb(204, 204, 204)',
                    showocean=True,
                    oceancolor='rgb(230, 245, 255)',
                    projection_type='natural earth'
                ),
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Location table
            with st.expander("Location Details"):
                loc_df = pd.DataFrame(locations)
                st.dataframe(loc_df[['name', 'type', 'mention_count']], use_container_width=True)
        else:
            st.info("No location data available")

def show_question_page(system):
    """Question Answering page"""
    st.header("Ask a Question")
    
    st.write("Enter a historical question about Chinese exploration:")
    
    question = st.text_area(
        "Your question:",
        height=100,
        placeholder="e.g., What was Zheng He's most significant voyage?"
    )
    
    if st.button("Research and Answer", type="primary"):
        if question:
            with st.spinner("Researching and analyzing..."):
                # Search for relevant documents
                results = system.semantic_search(question, k=5)
                
                if results:
                    st.success(f"Found {len(results)} relevant documents")
                    
                    # Display answer based on documents
                    st.subheader("Answer")
                    
                    # Create a summary from top documents
                    answer_parts = []
                    for i, result in enumerate(results[:3]):
                        answer_parts.append(f"**{result['title']}** by {result['author']} discusses this topic. {result['snippet']}")
                    
                    answer = " ".join(answer_parts)
                    
                    st.markdown(f"""
                    <div class='answer-container'>
                    {answer}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show sources
                    with st.expander("Sources"):
                        for i, result in enumerate(results[:3]):
                            st.write(f"{i+1}. **{result['title']}**")
                            st.write(f"   Author: {result['author']}")
                            st.write(f"   Type: {result['source_type']}")
                            if result['url']:
                                st.markdown(f"   [View Source]({result['url']})")
                            st.divider()
                else:
                    st.warning("No relevant documents found for your question")

def show_settings_page(system):
    """Settings page"""
    st.header("System Settings")
    
    # System info
    st.subheader("System Information")
    
    stats = system.get_database_stats()
    if stats:
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Database Status:**")
            st.write(f"- Documents: {stats['total_documents']}")
            st.write(f"- Entities: {stats['total_entities']}")
            st.write(f"- Vector Index: {'Loaded' if system.index else 'Not loaded'}")
        
        with col2:
            st.write("**File Paths:**")
            st.write(f"- Database: {system.db_path}")
            st.write(f"- Vector DB: {system.vector_dir}")
    
    # Actions
    st.divider()
    st.subheader("Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refresh System", use_container_width=True):
            st.cache_resource.clear()
            st.success("Cache cleared")
            st.rerun()
    
    with col2:
        if st.button("Check Database", use_container_width=True):
            if system.db:
                st.success("Database connection working")
            else:
                st.error("Database connection failed")

# ========== SIMPLIFIED MAIN APPLICATION ==========

def main():
    """Main application - SIMPLIFIED VERSION"""
    
    # Header
    st.markdown("<h1 class='main-header'>1421 Historical Research System</h1>", unsafe_allow_html=True)
    
    # Check if files exist FIRST
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "knowledge_base.db"
    vector_dir = base_dir / "data" / "vector_databases" / "main_index"
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            db_exists = db_path.exists()
            status = "✅" if db_exists else "❌"
            st.write(f"{status} Database: `{db_path.name}`")
            st.write(f"Path: `{db_path}`")
            st.write(f"Exists: {db_exists}")
            
        with col2:
            vector_exists = vector_dir.exists()
            status = "✅" if vector_exists else "❌"
            st.write(f"{status} Vector DB: `{vector_dir.name}`")
            st.write(f"Exists: {vector_exists}")
    
    if not db_path.exists():
        st.error("""
        ## Database file not found!
        
        **Please make sure:**
        1. The file `knowledge_base.db` is in the `data/` folder
        2. It's uploaded to GitHub
        3. File name is exactly `knowledge_base.db`
        
        **Current directory structure:**
        """)
        
        # Show directory contents
        import subprocess
        try:
            result = subprocess.run(['find', '.', '-type', 'f', '-name', '*.db'], 
                                  capture_output=True, text=True)
            st.code(result.stdout if result.stdout else "No .db files found")
        except:
            # Fallback to Python
            db_files = list(base_dir.glob('**/*.db'))
            st.code('\n'.join([str(f) for f in db_files]) if db_files else "No .db files found")
        
        st.stop()
    
    # Initialize system
    with st.spinner("Initializing system..."):
        system = init_system()
    
    if system is None:
        st.error("Failed to initialize system. Check the logs above.")
        st.stop()
    
    # Show status
    stats = system.get_database_stats()
    if stats:
        st.success(f"✅ System Ready: {stats['total_documents']} documents loaded")
    else:
        st.warning("System loaded but could not get database stats")
    
    # Simple sidebar
    with st.sidebar:
        st.title("Navigation")
        
        page = st.radio(
            "Go to:",
            ["Dashboard", "Research Documents", "Voyage Map", "Ask Question", "Settings"],
            label_visibility="collapsed"
        )
        
        st.session_state.current_page = page
        
        # Quick stats
        st.divider()
        st.write("**System Stats**")
        
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Documents", stats['total_documents'])
            with col2:
                st.metric("Vector DB", "Ready" if system.index else "Offline")
    
    # Page routing
    pages = {
        "Dashboard": show_dashboard,
        "Research Documents": show_documents_page,
        "Voyage Map": show_map_page,
        "Ask Question": show_question_page,
        "Settings": show_settings_page
    }
    
    current_page = st.session_state.get('current_page', 'Dashboard')
    if current_page in pages:
        pages[current_page](system)

if __name__ == "__main__":
    main()
