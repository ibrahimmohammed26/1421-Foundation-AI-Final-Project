"""
1421 Historical Research System - SIMPLIFIED VERSION
No external dependencies, just SQLite + Streamlit
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import threading
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
.main-header {
    font-size: 2.5rem;
    color: #000000;
    text-align: center;
    margin-bottom: 1.5rem;
    font-weight: 700;
}

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
</style>
""", unsafe_allow_html=True)

# ========== THREAD-SAFE DATABASE CONNECTION ==========

class DatabaseManager:
    """Thread-safe SQLite database manager"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.local = threading.local()
    
    def get_connection(self):
        """Get or create a thread-local database connection"""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
    
    def execute_query(self, query, params=None):
        """Execute a query and fetch all results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Query error: {e}")
            return []
    
    def get_stats(self):
        """Get database statistics"""
        try:
            # Check if tables exist
            tables = self.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            if not tables:
                return None
            
            # Get document count
            docs_result = self.execute_query("SELECT COUNT(*) as count FROM documents")
            total_docs = docs_result[0]['count'] if docs_result else 0
            
            # Get document types
            types_result = self.execute_query("SELECT source_type, COUNT(*) as count FROM documents GROUP BY source_type")
            docs_by_source = {row['source_type']: row['count'] for row in types_result} if types_result else {}
            
            # Get entity count
            entities_result = self.execute_query("SELECT COUNT(*) as count FROM entities")
            total_entities = entities_result[0]['count'] if entities_result else 0
            
            return {
                "total_documents": total_docs,
                "documents_by_source": docs_by_source,
                "total_entities": total_entities,
                "tables": [row['name'] for row in tables]
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return None
    
    def get_documents(self, limit=100, search_query=None, source_type=None):
        """Get documents from database"""
        try:
            if search_query:
                search_pattern = f"%{search_query}%"
                query = """
                    SELECT * FROM documents 
                    WHERE title LIKE ? OR content LIKE ? OR author LIKE ?
                    ORDER BY id LIMIT ?
                """
                params = (search_pattern, search_pattern, search_pattern, limit)
            elif source_type and source_type != "All":
                query = "SELECT * FROM documents WHERE source_type = ? ORDER BY id LIMIT ?"
                params = (source_type, limit)
            else:
                query = "SELECT * FROM documents ORDER BY id LIMIT ?"
                params = (limit,)
            
            results = self.execute_query(query, params)
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error getting documents: {e}")
            return []
    
    def get_locations(self):
        """Get location entities for map"""
        try:
            query = """
                SELECT entity_text, COUNT(*) as count 
                FROM entities 
                WHERE entity_type = 'LOCATION'
                GROUP BY entity_text
                ORDER BY count DESC
                LIMIT 50
            """
            results = self.execute_query(query)
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error getting locations: {e}")
            return []

# ========== INITIALIZE SYSTEM ==========

@st.cache_resource
def init_database():
    """Initialize database connection"""
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "knowledge_base.db"
    
    # Check if database exists
    if not db_path.exists():
        st.error(f"Database not found at: {db_path}")
        return None
    
    try:
        db = DatabaseManager(str(db_path))
        
        # Test connection
        stats = db.get_stats()
        if stats is None:
            st.error("Cannot connect to database")
            return None
        
        return db
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

# ========== PAGE FUNCTIONS ==========

def show_dashboard(db):
    """Dashboard page"""
    st.header("Dashboard")
    
    # Get stats
    stats = db.get_stats()
    
    if stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", stats['total_documents'])
        with col2:
            st.metric("Total Entities", stats['total_entities'])
        with col3:
            st.metric("Tables", len(stats['tables']))
    
    st.divider()
    
    # Quick search
    st.subheader("Quick Search")
    query = st.text_input("Search documents:", placeholder="Enter keywords...")
    
    if st.button("Search"):
        if query:
            with st.spinner("Searching..."):
                documents = db.get_documents(search_query=query, limit=10)
                
                if documents:
                    st.success(f"Found {len(documents)} documents")
                    
                    for i, doc in enumerate(documents[:3]):
                        with st.expander(f"{i+1}. {doc.get('title', 'Untitled')}"):
                            st.write(f"**Author:** {doc.get('author', 'Unknown')}")
                            st.write(f"**Type:** {doc.get('source_type', 'Unknown')}")
                            
                            # Show preview
                            content = doc.get('content', '')
                            if content:
                                st.write(content[:300] + "...")
                else:
                    st.warning("No documents found")

def show_documents(db):
    """Documents page"""
    st.header("Research Documents")
    
    # Search controls
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("Search:", placeholder="Title, author, or keywords")
    with col2:
        limit = st.selectbox("Results", [25, 50, 100], index=0)
    
    # Load documents
    if search_query:
        documents = db.get_documents(search_query=search_query, limit=limit)
        if documents:
            st.success(f"Found {len(documents)} documents for '{search_query}'")
        else:
            st.info("No documents found. Showing all documents...")
            documents = db.get_documents(limit=limit)
    else:
        documents = db.get_documents(limit=limit)
        st.info(f"Showing {len(documents)} documents")
    
    # Display results
    if documents:
        # Create table data
        table_data = []
        for doc in documents:
            table_data.append({
                'ID': doc.get('id', ''),
                'Title': doc.get('title', 'Untitled'),
                'Author': doc.get('author', 'Unknown'),
                'Type': doc.get('source_type', 'Unknown'),
                'Words': doc.get('word_count', 0),
                'URL': doc.get('url', '')[:50] + "..." if doc.get('url') and len(doc.get('url')) > 50 else doc.get('url', '')
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

def show_map(db):
    """Map page (simplified)"""
    st.header("Voyage Locations")
    
    locations = db.get_locations()
    
    if locations:
        # Create table
        location_data = []
        for loc in locations:
            location_data.append({
                'Location': loc['entity_text'],
                'Mention Count': loc['count']
            })
        
        df = pd.DataFrame(location_data)
        st.dataframe(df, use_container_width=True)
        
        # Show as markdown map (simplified)
        st.subheader("Geographical Distribution")
        
        # Known coordinates for common locations
        known_locations = {
            'China': '📍 China (35°N, 104°E)',
            'Beijing': '📍 Beijing (39°N, 116°E)',
            'India': '📍 India (20°N, 78°E)',
            'Africa': '📍 Africa (8°N, 34°E)',
            'America': '📍 America (37°N, 95°W)',
            'Pacific Ocean': '📍 Pacific Ocean (0°, 160°W)',
        }
        
        map_text = "### Key Historical Locations:\n\n"
        for loc in locations[:10]:  # Show top 10
            loc_name = loc['entity_text']
            if loc_name in known_locations:
                map_text += f"{known_locations[loc_name]} - Mentioned {loc['count']} times\n"
        
        st.markdown(map_text)
    else:
        st.info("No location data available")

def show_question(db):
    """Question page (simplified)"""
    st.header("Ask a Question")
    
    question = st.text_area(
        "Your historical question:",
        height=100,
        placeholder="e.g., What was Zheng He's most significant voyage?"
    )
    
    if st.button("Search for Answers"):
        if question:
            with st.spinner("Searching documents..."):
                # Search for relevant documents
                documents = db.get_documents(search_query=question, limit=5)
                
                if documents:
                    st.success(f"Found {len(documents)} relevant documents")
                    
                    # Display summary
                    st.subheader("Research Findings")
                    
                    for i, doc in enumerate(documents):
                        st.write(f"**{i+1}. {doc.get('title', 'Untitled')}**")
                        st.write(f"*By: {doc.get('author', 'Unknown')}*")
                        
                        # Show relevant excerpt
                        content = doc.get('content', '')
                        if content:
                            # Find question keywords in content
                            keywords = question.lower().split()
                            for keyword in keywords[:3]:  # Check first 3 keywords
                                if len(keyword) > 3 and keyword in content.lower():
                                    idx = content.lower().find(keyword)
                                    start = max(0, idx - 150)
                                    end = min(len(content), idx + 150)
                                    st.write(f"*Excerpt:* {content[start:end]}...")
                                    break
                            else:
                                st.write(f"*Excerpt:* {content[:200]}...")
                        
                        st.divider()
                else:
                    st.warning("No relevant documents found")

def show_settings(db):
    """Settings page"""
    st.header("System Settings")
    
    # Database info
    stats = db.get_stats()
    if stats:
        st.subheader("Database Information")
        st.write(f"- **Documents:** {stats['total_documents']}")
        st.write(f"- **Entities:** {stats['total_entities']}")
        st.write(f"- **Tables:** {', '.join(stats['tables'])}")
    
    # File info
    st.subheader("File Information")
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "knowledge_base.db"
    
    if db_path.exists():
        file_size = db_path.stat().st_size / (1024*1024)  # MB
        st.write(f"- **Database:** {db_path.name}")
        st.write(f"- **Size:** {file_size:.2f} MB")
        st.write(f"- **Path:** `{db_path}`")
    else:
        st.error(f"Database file not found: {db_path}")
    
    # Actions
    st.subheader("Actions")
    
    if st.button("Clear Cache", use_container_width=True):
        st.cache_resource.clear()
        st.success("Cache cleared")
        st.rerun()
    
    if st.button("Check Database", use_container_width=True):
        if db:
            st.success("Database connection is working")
        else:
            st.error("Database connection failed")

# ========== MAIN APPLICATION ==========

def main():
    """Main application"""
    
    # Header
    st.markdown("<h1 class='main-header'>1421 Historical Research System</h1>", unsafe_allow_html=True)
    
    # Initialize database
    with st.spinner("Connecting to database..."):
        db = init_database()
    
    if db is None:
        st.error("""
        ## Database Connection Failed
        
        **Please ensure:**
        1. The file `knowledge_base.db` exists in the `data/` folder
        2. The database file is properly uploaded to GitHub
        3. The file is not corrupted
        
        **For Streamlit Cloud:**
        - Go to "Manage App" → check the file structure
        - Make sure `data/knowledge_base.db` exists
        """)
        
        # Show current directory structure
        try:
            import subprocess
            result = subprocess.run(['find', '.', '-name', '*.db', '-type', 'f'], 
                                  capture_output=True, text=True)
            st.code(f"Database files found:\n{result.stdout}")
        except:
            pass
        
        return
    
    # Get stats for status display
    stats = db.get_stats()
    if stats and stats['total_documents'] > 0:
        st.markdown(f"""
        <div class='status-badge status-loaded'>
            ✅ System Ready: {stats['total_documents']} documents loaded
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Database connected but no documents found")
    
    # Sidebar navigation
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
        st.write("**Database Stats**")
        
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Documents", stats['total_documents'])
            with col2:
                st.metric("Entities", stats['total_entities'])
    
    # Page routing
    pages = {
        "Dashboard": show_dashboard,
        "Research Documents": show_documents,
        "Voyage Map": show_map,
        "Ask Question": show_question,
        "Settings": show_settings
    }
    
    current_page = st.session_state.get('current_page', 'Dashboard')
    if current_page in pages:
        pages[current_page](db)

if __name__ == "__main__":
    main()
