"""
1421 Research System - Unified Version for Streamlit Cloud
No FastAPI backend needed - everything runs in Streamlit
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
from typing import List, Dict, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import pytz
from collections import Counter
import sys
import os

# Set page config FIRST
st.set_page_config(
    page_title="1421 Historical Research System",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS STYLING ==========
st.markdown("""
<style>
/* Your CSS styling here */
</style>
""", unsafe_allow_html=True)

# ========== UNIFIED BACKEND CLASS ==========

class UnifiedResearchSystem:
    """Combined backend that runs entirely within Streamlit"""
    
    def __init__(self):
        # Set paths for Streamlit Cloud
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        
        # Database path
        self.db_path = self.data_dir / "knowledge_base.db"
        self.vector_dir = self.data_dir / "vector_databases" / "main_index"
        
        # Initialize components
        self.conn = None
        self.index = None
        self.documents = []
        self.metadatas = []
        self.model = None
        
        # Load everything
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize all components"""
        try:
            # 1. Connect to SQLite database
            if self.db_path.exists():
                self.conn = sqlite3.connect(str(self.db_path))
                self.conn.row_factory = sqlite3.Row
                st.session_state.db_loaded = True
            else:
                st.error(f"Database not found at: {self.db_path}")
                st.session_state.db_loaded = False
                return
            
            # 2. Load vector database
            index_file = self.vector_dir / "faiss_index.bin"
            metadata_file = self.vector_dir / "faiss_metadata.pkl"
            
            if index_file.exists() and metadata_file.exists():
                self.index = faiss.read_index(str(index_file))
                with open(metadata_file, 'rb') as f:
                    metadata = pickle.load(f)
                    self.documents = metadata.get('documents', [])
                    self.metadatas = metadata.get('metadatas', [])
                st.session_state.vector_loaded = True
            else:
                st.warning(f"Vector database not found at: {self.vector_dir}")
                st.session_state.vector_loaded = False
            
            # 3. Load embedding model (cache it)
            @st.cache_resource
            def load_model():
                return SentenceTransformer('all-MiniLM-L6-v2')
            
            self.model = load_model()
            
            st.session_state.system_initialized = True
            
        except Exception as e:
            st.error(f"Initialization error: {str(e)}")
            st.session_state.system_initialized = False
    
    def get_database_stats(self):
        """Get database statistics"""
        if not self.conn:
            return None
        
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]
        
        cursor.execute("SELECT source_type, COUNT(*) FROM documents GROUP BY source_type")
        docs_by_source = dict(cursor.fetchall())
        
        cursor.execute("SELECT COUNT(*) FROM entities")
        total_entities = cursor.fetchone()[0]
        
        cursor.execute("SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type")
        entities_by_type = dict(cursor.fetchall())
        
        return {
            "total_documents": total_docs,
            "documents_by_source": docs_by_source,
            "total_entities": total_entities,
            "entities_by_type": entities_by_type,
            "vector_documents": len(self.documents) if self.documents else 0
        }
    
    def get_all_documents(self, limit: int = 100, source_type: str = None):
        """Get all documents from database"""
        if not self.conn:
            return []
        
        cursor = self.conn.cursor()
        
        if source_type and source_type != "All":
            cursor.execute("""
                SELECT * FROM documents 
                WHERE source_type = ? 
                ORDER BY id 
                LIMIT ?
            """, (source_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM documents 
                ORDER BY id 
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        documents = [dict(row) for row in rows]
        return documents
    
    def semantic_search(self, query: str, k: int = 10):
        """Perform semantic search"""
        if not self.index or not self.model:
            return []
        
        try:
            # Encode query
            query_embedding = self.model.encode(
                [query], 
                convert_to_numpy=True, 
                normalize_embeddings=True
            ).astype('float32')
            
            # Search
            distances, indices = self.index.search(query_embedding, k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.metadatas):
                    doc_id = self.metadatas[idx]['id']
                    doc_details = self.get_document_details(doc_id)
                    
                    if doc_details:
                        results.append({
                            'document_id': doc_id,
                            'title': doc_details['title'],
                            'author': doc_details['author'],
                            'source_type': doc_details['source_type'],
                            'url': doc_details.get('url', ''),
                            'word_count': doc_details.get('word_count', 0),
                            'snippet': doc_details.get('content', '')[:300] + "...",
                            'similarity': float(1.0 / (1.0 + distances[0][i])),
                            'distance': float(distances[0][i])
                        })
            
            return results
            
        except Exception as e:
            st.error(f"Search error: {str(e)}")
            return []
    
    def get_document_details(self, doc_id: int):
        """Get full document details"""
        if not self.conn:
            return None
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def search_documents_sql(self, search_term: str, limit: int = 50):
        """Search documents using SQL LIKE (fallback)"""
        if not self.conn:
            return []
        
        cursor = self.conn.cursor()
        search_pattern = f"%{search_term}%"
        
        cursor.execute("""
            SELECT * FROM documents 
            WHERE title LIKE ? OR content LIKE ? OR author LIKE ?
            ORDER BY id 
            LIMIT ?
        """, (search_pattern, search_pattern, search_pattern, limit))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_entities(self, entity_type: str = None, limit: int = 50):
        """Get entities from database"""
        if not self.conn:
            return []
        
        cursor = self.conn.cursor()
        
        if entity_type:
            cursor.execute("""
                SELECT entity_text, entity_type, COUNT(*) as count 
                FROM entities 
                WHERE entity_type = ? 
                GROUP BY entity_text 
                ORDER BY count DESC 
                LIMIT ?
            """, (entity_type, limit))
        else:
            cursor.execute("""
                SELECT entity_text, entity_type, COUNT(*) as count 
                FROM entities 
                GROUP BY entity_text, entity_type 
                ORDER BY count DESC 
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_map_locations(self):
        """Get geographical locations"""
        locations_data = self.get_entities(entity_type='LOCATION', limit=50)
        
        # Mock coordinates for known locations
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
            'Calicut': (11.2588, 75.7804)
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
def initialize_system():
    """Initialize the research system (cached)"""
    system = UnifiedResearchSystem()
    return system

# ========== PAGE FUNCTIONS ==========

def show_dashboard(system):
    """Dashboard page"""
    st.header("Research Dashboard")
    
    # Get stats
    stats = system.get_database_stats()
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", stats['total_documents'])
        with col2:
            st.metric("Entities", stats['total_entities'])
        with col3:
            st.metric("Vector Docs", stats['vector_documents'])
        with col4:
            st.metric("Sources", len(stats['documents_by_source']))
    
    st.divider()
    
    # Quick search
    st.subheader("Quick Search")
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("Search the database:", placeholder="Enter search terms...")
    with col2:
        search_btn = st.button("Search", use_container_width=True)
    
    if search_btn and search_query:
        with st.spinner("Searching..."):
            results = system.semantic_search(search_query, k=10)
            
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
                sql_results = system.search_documents_sql(search_query)
                if sql_results:
                    st.success(f"Found {len(sql_results)} documents using keyword search")
                else:
                    st.warning("No documents found")

def show_documents_page(system):
    """Documents page"""
    st.header("Research Documents")
    
    # Initialize session state for pagination
    if 'doc_page' not in st.session_state:
        st.session_state.doc_page = 0
    if 'doc_source_filter' not in st.session_state:
        st.session_state.doc_source_filter = "All"
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("Search documents:", placeholder="Title, author, or keywords")
    with col2:
        source_filter = st.selectbox(
            "Filter by type",
            ["All", "Book", "Article", "Research Paper", "Website"],
            key="doc_source_filter"
        )
    with col3:
        limit = st.selectbox("Results", [25, 50, 100], index=0)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        search_btn = st.button("Search Documents", type="primary", use_container_width=True)
    with col2:
        show_all_btn = st.button("Show All Documents", use_container_width=True)
    
    # Load documents
    documents = []
    
    if search_btn and search_term:
        with st.spinner("Searching documents..."):
            # Try semantic search first
            documents = system.semantic_search(search_term, k=limit)
            if not documents:
                # Fallback to SQL search
                documents = system.search_documents_sql(search_term, limit=limit)
    
    elif show_all_btn or (not search_term and not search_btn):
        with st.spinner("Loading all documents..."):
            documents = system.get_all_documents(limit=limit, source_type=source_filter)
    
    # Display results
    if documents:
        st.success(f"Loaded {len(documents)} documents")
        
        # Create dataframe for display
        df_data = []
        for doc in documents:
            df_data.append({
                'ID': doc.get('id') or doc.get('document_id', ''),
                'Title': doc.get('title', 'Untitled'),
                'Author': doc.get('author', 'Unknown'),
                'Type': doc.get('source_type', 'Unknown'),
                'Words': doc.get('word_count', 0),
                'URL': doc.get('url', '')[:50] + "..." if len(doc.get('url', '')) > 50 else doc.get('url', '')
            })
        
        df = pd.DataFrame(df_data)
        
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
            label="Download as CSV",
            data=csv,
            file_name=f"documents_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    else:
        st.info("No documents to display. Use the search or 'Show All' button.")

def show_map_page(system):
    """Map page"""
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
            
            fig.add_trace(go.Scattergeo(
                lon=lons,
                lat=lats,
                mode='markers+text',
                marker=dict(
                    size=10,
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
                height=600,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Location table
            with st.expander("Location Details"):
                loc_df = pd.DataFrame(locations)
                st.dataframe(loc_df[['name', 'type', 'mention_count']], use_container_width=True)
        else:
            st.info("No location data available")

def show_question_page(system):
    """Question answering page"""
    st.header("Ask a Question")
    
    st.write("Enter a historical question about Chinese exploration:")
    
    question = st.text_area(
        "Your question:",
        height=100,
        placeholder="e.g., What was Zheng He's most significant voyage?"
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        ask_btn = st.button("Ask Question", type="primary", use_container_width=True)
    
    if ask_btn and question:
        with st.spinner("Researching and analyzing..."):
            # First, search for relevant documents
            search_results = system.semantic_search(question, k=5)
            
            if search_results:
                # Prepare context from top results
                context_parts = []
                for result in search_results[:3]:
                    doc_id = result['document_id']
                    doc_details = system.get_document_details(doc_id)
                    if doc_details:
                        context_parts.append(
                            f"Source: {doc_details['title']} by {doc_details['author']}\n"
                            f"Content: {doc_details.get('content', '')[:500]}"
                        )
                
                if context_parts:
                    # For now, show the search results
                    st.subheader("Answer Based on Research")
                    st.info("Note: AI question answering requires OpenAI API integration")
                    
                    st.write("**Relevant documents found:**")
                    for i, result in enumerate(search_results[:3]):
                        st.write(f"{i+1}. **{result['title']}**")
                        st.write(f"   Author: {result['author']}")
                        st.write(f"   Relevance: {result['similarity']:.1%}")
                        st.write(f"   Excerpt: {result['snippet']}")
                        st.divider()
                else:
                    st.warning("No relevant documents found in the database")
            else:
                st.warning("No results found for your question")

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
    
    # Database management
    st.divider()
    st.subheader("Database Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refresh Database", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("Clear Cache", use_container_width=True):
            st.cache_resource.clear()
            st.success("Cache cleared")
            st.rerun()
    
    # Debug information
    with st.expander("Debug Information"):
        st.write("**Session State:**")
        st.json({k: str(v) for k, v in st.session_state.items()})
        
        st.write("**System Check:**")
        checks = {
            "Database connection": system.conn is not None,
            "Vector index loaded": system.index is not None,
            "Embedding model loaded": system.model is not None,
            "Documents in vector DB": len(system.documents) > 0
        }
        
        for check, status in checks.items():
            st.write(f"- {check}: {'✅' if status else '❌'}")

# ========== MAIN APP ==========

def main():
    """Main application"""
    
    # Initialize system
    system = initialize_system()
    
    # Check if system initialized
    if not st.session_state.get('system_initialized', False):
        st.error("System initialization failed. Please check:")
        st.write(f"1. Database exists at: {system.db_path}")
        st.write(f"2. Vector database exists at: {system.vector_dir}")
        st.write(f"3. Files are properly uploaded to Streamlit Cloud")
        return
    
    # Header
    st.markdown("<h1 class='main-header'>1421 Historical Research System</h1>", unsafe_allow_html=True)
    
    # Status indicator
    stats = system.get_database_stats()
    if stats and stats['total_documents'] > 0:
        st.success(f"✅ System Ready: {stats['total_documents']} documents loaded")
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        
        # Navigation buttons
        pages = {
            "Dashboard": show_dashboard,
            "Research Documents": show_documents_page,
            "Voyage Map": show_map_page,
            "Ask Question": show_question_page,
            "Settings": show_settings_page
        }
        
        for page_name in pages.keys():
            if st.button(page_name, use_container_width=True, key=f"nav_{page_name}"):
                st.session_state.current_page = page_name
                st.rerun()
        
        # Set default page
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Dashboard"
        
        # Quick stats
        st.divider()
        st.write("**Database Stats**")
        
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Documents", stats['total_documents'])
            with col2:
                st.metric("Vector Docs", stats['vector_documents'])
    
    # Show current page
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
