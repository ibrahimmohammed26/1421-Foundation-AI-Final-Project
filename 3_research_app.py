"""
PDD-Compliant Frontend
Objective 2.4: Web interface connected to backend API
UPDATED FOR WORKING BACKEND API
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import re
from typing import List, Dict, Any
import webbrowser
import time

# Page config
st.set_page_config(
    page_title="1421 AI Research System",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration - CONNECT TO YOUR WORKING BACKEND
API_BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    color: #1a237e;
    text-align: center;
    margin-bottom: 0.5rem;
    font-weight: 700;
}
.sub-header {
    text-align: center;
    color: #5d4037;
    margin-bottom: 2rem;
    font-size: 1.1rem;
}
.feature-badge {
    display: inline-block;
    background: #e3f2fd;
    color: #1565c0;
    padding: 6px 14px;
    margin: 4px;
    border-radius: 16px;
    font-size: 0.85em;
    font-weight: 600;
    border: 1px solid #bbdefb;
}
.citation {
    background: #f5f5f5;
    border-left: 4px solid #4CAF50;
    padding: 10px;
    margin: 5px 0;
    border-radius: 4px;
    font-size: 0.9em;
}
.answer-box {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    margin: 15px 0;
}
.stats-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}
.document-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    background: white;
}
.search-result {
    padding: 15px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin: 10px 0;
    background: #f9f9f9;
}
.chat-bubble-user {
    background: #007bff;
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0;
    max-width: 80%;
    margin-left: auto;
}
.chat-bubble-assistant {
    background: #f1f1f1;
    color: #333;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 0;
    max-width: 80%;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

class APIClient:
    """Client for backend API - UPDATED FOR WORKING ENDPOINTS"""

    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url

    def health_check(self):
        """Check API health - UPDATED ENDPOINT"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Health check failed: {e}")
            return False

    def search_documents(self, query: str, limit: int = 10):
        """Search documents via API - UPDATED FOR WORKING ENDPOINT"""
        try:
            payload = {
                "query": query,
                "limit": limit
            }

            response = requests.post(
                f"{self.base_url}/search",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                st.error(f"Search error: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Search API error: {e}")
            return []

    def ask_question(self, question: str, use_openai: bool = True):
        """Ask question via RAG API - UPDATED FOR WORKING ENDPOINT"""
        try:
            payload = {
                "query": question,
                "use_openai": use_openai
            }

            response = requests.post(
                f"{self.base_url}/ask",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Ask error: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Ask API error: {e}")
            return None

    def get_entities(self, entity_type: str = None, limit: int = 50):
        """Get entities via API - UPDATED FOR WORKING ENDPOINT"""
        try:
            params = {"limit": limit}
            if entity_type:
                params["entity_type"] = entity_type

            response = requests.get(
                f"{self.base_url}/entities",
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Entities error: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Entities API error: {e}")
            return []

    def get_stats(self):
        """Get system statistics - UPDATED FOR WORKING ENDPOINT"""
        try:
            response = requests.get(f"{self.base_url}/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Stats error: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Stats API error: {e}")
            return None

    def get_document(self, doc_id: int):
        """Get document details by ID"""
        try:
            response = requests.get(f"{self.base_url}/document/{doc_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

def create_timeline_visualization(events: List[Dict]):
    """Create timeline visualization from events"""
    if not events:
        return None

    df = pd.DataFrame(events)

    fig = px.scatter(
        df,
        x='year',
        y='type',
        color='type',
        hover_data=['description', 'context'],
        title="Historical Timeline",
        height=400
    )

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Event Type",
        showlegend=True
    )

    return fig

def create_entity_chart(entities: List[Dict]):
    """Create entity frequency chart"""
    if not entities:
        return None

    df = pd.DataFrame(entities)

    # Group by entity type
    type_counts = df.groupby('entity_type').size().reset_index(name='count')

    fig = px.bar(
        type_counts,
        x='entity_type',
        y='count',
        color='entity_type',
        title="Entities by Type",
        labels={'entity_type': 'Entity Type', 'count': 'Count'}
    )

    return fig

def extract_timeline_from_documents(documents: List[Dict]):
    """Extract timeline events from documents"""
    events = []

    for doc in documents:
        # Extract years from content
        content = doc.get('content', '')
        years = re.findall(r'\b(1[3-9]\d{2})\b', content)

        for year in years[:3]:  # Limit to first 3 years per document
            events.append({
                'year': int(year),
                'description': doc.get('title', 'Untitled')[:100],
                'type': 'Document',
                'context': content[:200] + '...'
            })

    return events

def main():
    """Main Streamlit app"""

    # Initialize API client
    api_client = APIClient()

    # Initialize session state
    if 'saved_searches' not in st.session_state:
        st.session_state.saved_searches = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []

    # Header
    st.markdown('<h1 class="main-header">🧭 1421 AI Research System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">PDD-Compliant AI Research Assistant</p>', unsafe_allow_html=True)

    # Check API health
    with st.spinner("🔌 Connecting to backend..."):
        api_healthy = api_client.health_check()

    if not api_healthy:
        st.error("""
        ## ❌ Backend API Not Available
        
        **To fix this:**
        
        1. **Make sure the backend is running** (you should see in terminal):
           ```
           ✅ Vector database loaded: 347 documents
           ✅ Backend initialized
           🚀 Starting 1421 Research API server...
           ```
        
        2. **Start the backend** (in a new terminal):
           ```bash
           python scripts/2_backend_api.py
           ```
        
        3. **Check it's accessible** at:
           http://localhost:8000
        
        4. **Refresh this page** after the backend starts
        """)

        # Quick start instructions
        with st.expander("🚀 Quick Start Instructions", expanded=True):
            st.code("""
            # Terminal 1 - Start Backend
            python scripts/2_backend_api.py
            
            # Terminal 2 - Start Frontend  
            streamlit run scripts/3_research_app.py
            
            # Then open:
            # - Backend API: http://localhost:8000
            # - Frontend App: http://localhost:8501
            # - API Docs: http://localhost:8000/docs
            """, language="bash")

        st.stop()

    # Sidebar
    with st.sidebar:
        st.header("📊 System Status")

        # Get and display stats
        stats = api_client.get_stats()
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📄 Documents", stats.get('total_documents', 0))
            with col2:
                st.metric("🔤 Entities", stats.get('total_entities', 0))

            # Show entity breakdown
            with st.expander("Entity Statistics", expanded=False):
                entities_by_type = stats.get('entities_by_type', {})
                for entity_type, count in entities_by_type.items():
                    st.progress(
                        min(count / max(entities_by_type.values(), default=1), 1),
                        text=f"{entity_type}: {count:,}"
                    )

        st.divider()

        # Navigation
        st.header("📍 Navigation")
        page = st.radio(
            "Go to",
            ["🏠 Dashboard", "🔍 Research Assistant", "📚 Document Search",
             "📊 Analytics", "⚙️ Settings", "📖 API Docs"]
        )

        st.divider()

        # Quick Actions
        st.header("⚡ Quick Actions")

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.session_state.pop('stats', None)
            st.rerun()

        if st.button("📖 Open API Docs", use_container_width=True):
            webbrowser.open_new_tab(f"{API_BASE_URL}/docs")

        if st.button("🐛 View Backend Logs", use_container_width=True):
            st.info("Backend logs are in the terminal where you ran `python scripts/2_backend_api.py`")

        st.divider()

        # Recent Searches
        st.header("💾 Recent Searches")
        if st.session_state.saved_searches:
            for i, search in enumerate(reversed(st.session_state.saved_searches[-3:])):
                if st.button(f"🔍 {search[:40]}...", key=f"search_{i}", use_container_width=True):
                    st.session_state.search_query = search
                    st.session_state.page = "Document Search"
                    st.rerun()
        else:
            st.info("No recent searches")

        st.divider()

        # OpenAI Settings
        st.header("🤖 AI Settings")
        use_openai = st.checkbox("Use OpenAI (RAG)", value=True,
                                help="Use OpenAI for better answers. Requires API key in backend.")

        st.session_state.use_openai = use_openai

    # Main content based on navigation
    if page == "🏠 Dashboard":
        show_dashboard(api_client, stats)
    elif page == "🔍 Research Assistant":
        show_research_assistant(api_client)
    elif page == "📚 Document Search":
        show_document_search(api_client)
    elif page == "📊 Analytics":
        show_analytics(api_client, stats)
    elif page == "⚙️ Settings":
        show_settings(api_client)
    elif page == "📖 API Docs":
        show_api_docs()

def show_dashboard(api_client, stats):
    """Show dashboard overview"""
    st.header("🏠 Dashboard")
    st.markdown("Welcome to the 1421 Research System")

    # Stats cards
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", stats.get('total_documents', 0))
        with col2:
            st.metric("Total Entities", stats.get('total_entities', 0))
        with col3:
            source_count = len(stats.get('documents_by_source', {}))
            st.metric("Source Types", source_count)
        with col4:
            st.metric("Vector Database", "347 docs")

    # Quick Search
    st.subheader("🔍 Quick Search")
    quick_query = st.text_input("Search for documents...", key="quick_search")

    if st.button("Quick Search", type="primary") and quick_query:
        with st.spinner("Searching..."):
            results = api_client.search_documents(quick_query, limit=5)
            st.session_state.search_results = results
            st.session_state.saved_searches.append(quick_query)

        if results:
            st.success(f"Found {len(results)} results")
            for i, result in enumerate(results[:3]):
                with st.container():
                    st.write(f"**{i+1}. {result.get('title', 'Untitled')}**")
                    st.write(f"*By {result.get('author', 'Unknown')}*")
                    st.write(f"Relevance: **{result.get('distance', 0):.4f}**")
                    st.write(result.get('content', '')[:200] + "...")
                    st.divider()
        else:
            st.warning("No results found")

    # Recent Activity
    st.subheader("📈 Recent Activity")

    if st.session_state.saved_searches:
        activity_df = pd.DataFrame({
            'Search': st.session_state.saved_searches[-5:],
            'Time': [datetime.now().strftime("%H:%M") for _ in range(min(5, len(st.session_state.saved_searches)))]
        })
        st.dataframe(activity_df, use_container_width=True, hide_index=True)
    else:
        st.info("No recent activity")

def show_research_assistant(api_client):
    """Show RAG research assistant"""
    st.header("🤖 Research Assistant")
    st.markdown("Ask research questions. The AI will answer using the 1421 research database.")

    # Example questions
    st.subheader("💡 Example Questions")
    examples = [
        "What was Zheng He's most significant voyage?",
        "How does Gavin Menzies support his theory about Chinese discovery of America?",
        "What Ming Dynasty artifacts have been found in America?",
        "What evidence exists for Chinese exploration before Columbus?"
    ]

    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(example, key=f"ex_{i}", use_container_width=True):
                st.session_state.question_input = example
                st.rerun()

    # Question input
    st.subheader("💬 Ask a Question")
    question = st.text_area(
        "Your research question:",
        value=st.session_state.get('question_input', ''),
        height=100,
        placeholder="Example: What evidence exists for Chinese exploration of the Americas before 1492?",
        key="question_area"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        ask_button = st.button("🤖 Ask AI", type="primary", use_container_width=True)
    with col2:
        if st.button("🗑️ Clear", type="secondary", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    if ask_button and question:
        with st.spinner("🔍 Researching and analyzing..."):
            # Save to history
            if question not in st.session_state.saved_searches:
                st.session_state.saved_searches.append(question)

            # Get answer from RAG system
            result = api_client.ask_question(
                question,
                use_openai=st.session_state.get('use_openai', True)
            )

            if result:
                # Add to chat history
                st.session_state.chat_history.append({
                    "question": question,
                    "answer": result.get("answer", "No answer available"),
                    "sources": result.get("sources", []),
                    "timestamp": datetime.now().isoformat()
                })

    # Display chat history
    if st.session_state.chat_history:
        st.subheader("📝 Conversation History")

        for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
            with st.expander(f"Q: {chat['question'][:60]}...", expanded=(i==0)):
                # Question
                st.markdown(f"**Question:** {chat['question']}")

                # Answer
                st.markdown('<div class="answer-box">', unsafe_allow_html=True)
                st.markdown(chat['answer'])
                st.markdown('</div>', unsafe_allow_html=True)

                # Sources
                if chat.get('sources'):
                    st.markdown("**📚 Sources Cited:**")
                    for j, source in enumerate(chat['sources'][:3]):
                        with st.container():
                            st.markdown(f"""
                            **{j+1}. {source.get('title', 'Untitled')}**  
                            *By {source.get('author', 'Unknown')}*
                            """)

                            if source.get('url'):
                                st.markdown(f"[🔗 Open Source]({source['url']})")

                st.caption(f"Answered at {datetime.fromisoformat(chat['timestamp']).strftime('%H:%M')}")

def show_document_search(api_client):
    """Show document search interface"""
    st.header("📚 Document Search")
    st.markdown("Search through the research documents.")

    # Search input
    search_query = st.text_input(
        "Search documents:",
        value=st.session_state.get('search_query', ''),
        placeholder="Enter keywords, names, or topics...",
        key="search_input"
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        limit = st.slider("Results to show", 5, 50, 10)
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    with col3:
        if st.button("🗑️ Clear Results", type="secondary", use_container_width=True):
            st.session_state.search_results = []
            st.rerun()

    if search_button and search_query:
        with st.spinner("Searching documents..."):
            results = api_client.search_documents(
                query=search_query,
                limit=limit
            )

            # Save search
            if search_query not in st.session_state.saved_searches:
                st.session_state.saved_searches.append(search_query)

            st.session_state.search_results = results

            if results:
                st.success(f"Found {len(results)} documents")
            else:
                st.warning("No documents found. Try a different search query.")

    # Display results
    if st.session_state.search_results:
        st.subheader("📋 Search Results")

        for i, doc in enumerate(st.session_state.search_results):
            with st.container():
                # Card header
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{i+1}. {doc.get('title', 'Untitled')}**")
                    st.write(f"*By {doc.get('author', 'Unknown')} • {doc.get('source_type', 'Unknown')}*")

                with col2:
                    distance = doc.get('distance', 0)
                    if distance < 0.5:
                        st.success(f"Relevance: {distance:.4f}")
                    elif distance < 0.8:
                        st.warning(f"Relevance: {distance:.4f}")
                    else:
                        st.error(f"Relevance: {distance:.4f}")

                # Content preview
                st.write(doc.get('content', '')[:300] + "...")

                # Actions
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📖 View Details", key=f"view_{i}"):
                        st.session_state.selected_doc_id = doc.get('document_id')
                        show_document_details(api_client, doc.get('document_id'))
                with col2:
                    if st.button(f"💬 Ask about this", key=f"ask_{i}"):
                        st.session_state.question_input = f"Tell me about: {doc.get('title', 'this document')}"
                        st.switch_page("🔍 Research Assistant")

                st.divider()

def show_document_details(api_client, doc_id):
    """Show detailed document view"""
    if not doc_id:
        return

    with st.spinner("Loading document..."):
        doc = api_client.get_document(doc_id)

    if doc:
        st.subheader("📄 Document Details")

        # Document info
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Title:** {doc.get('title', 'Untitled')}")
            st.write(f"**Author:** {doc.get('author', 'Unknown')}")
            st.write(f"**Source Type:** {doc.get('source_type', 'Unknown')}")
        with col2:
            st.write(f"**Word Count:** {doc.get('word_count', 0):,}")
            st.write(f"**Imported:** {doc.get('import_date', 'Unknown')}")
            if doc.get('url'):
                st.write(f"**URL:** [{doc['url'][:50]}...]({doc['url']})")

        # Content
        st.subheader("📝 Content")
        st.text_area("", doc.get('content', ''), height=300, disabled=True)

        # Entities
        if 'entities' in doc and doc['entities']:
            st.subheader("🔤 Entities Found")
            entity_cols = st.columns(3)
            entity_types = {}

            for entity in doc['entities']:
                entity_type = entity.get('type', 'UNKNOWN')
                if entity_type not in entity_types:
                    entity_types[entity_type] = []
                entity_types[entity_type].append(entity.get('text', ''))

            for i, (entity_type, entities) in enumerate(entity_types.items()):
                with entity_cols[i % 3]:
                    with st.expander(f"{entity_type} ({len(entities)})", expanded=True):
                        for entity_text in entities[:10]:  # Limit to 10 per type
                            st.write(f"• {entity_text}")

        # Back button
        if st.button("← Back to Search"):
            st.session_state.pop('selected_doc_id', None)
            st.rerun()
    else:
        st.error("Document not found")

def show_analytics(api_client, stats):
    """Show analytics and visualizations"""
    st.header("📊 Analytics")

    if not stats:
        st.info("No statistics available")
        return

    # Entity analysis
    st.subheader("🔤 Entity Analysis")

    # Get detailed entities
    entities = api_client.get_entities(limit=100)

    if isinstance(entities, list) and entities:
        entity_df = pd.DataFrame(entities)

        # Entity type distribution
        if 'entity_type' in entity_df.columns:
            type_counts = entity_df['entity_type'].value_counts().reset_index()
            type_counts.columns = ['Entity Type', 'Count']

            fig1 = px.pie(
                type_counts,
                values='Count',
                names='Entity Type',
                title='Entities by Type',
                hole=0.4
            )
            st.plotly_chart(fig1, use_container_width=True)

        # Top entities
        if 'count' in entity_df.columns and 'entity_text' in entity_df.columns:
            top_entities = entity_df.sort_values('count', ascending=False).head(20)

            fig2 = px.bar(
                top_entities,
                x='count',
                y='entity_text',
                orientation='h',
                title='Top 20 Entities',
                labels={'entity_text': 'Entity', 'count': 'Frequency'}
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Timeline visualization
    st.subheader("📅 Timeline Analysis")

    # Extract timeline from recent documents
    if st.session_state.get('search_results'):
        events = extract_timeline_from_documents(st.session_state.search_results)

        if events:
            fig3 = create_timeline_visualization(events)
            if fig3:
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No timeline events found in current search results")
    else:
        st.info("Perform a search to see timeline analysis")

def show_settings(api_client):
    """Show settings panel"""
    st.header("⚙️ Settings")

    st.subheader("API Configuration")

    col1, col2 = st.columns(2)
    with col1:
        api_url = st.text_input("API Base URL", value=API_BASE_URL)
    with col2:
        st.text_input("OpenAI API Key", value="Configured in backend", type="password", disabled=True)

    st.info("OpenAI API key should be configured in `2_backend_api.py`")

    st.subheader("Search Settings")

    col1, col2 = st.columns(2)
    with col1:
        default_limit = st.number_input("Default search results", 5, 100, 10)
    with col2:
        auto_save = st.checkbox("Auto-save searches", value=True)

    st.subheader("System Information")

    info_cols = st.columns(2)
    with info_cols[0]:
        st.write("**Backend Status:**")
        if api_client.health_check():
            st.success("✅ Online")
        else:
            st.error("❌ Offline")

        st.write("**API Version:**")
        st.code("v1.0.0")

    with info_cols[1]:
        st.write("**Data Statistics:**")
        stats = api_client.get_stats()
        if stats:
            st.write(f"Documents: {stats.get('total_documents', 0)}")
            st.write(f"Entities: {stats.get('total_entities', 0)}")
        else:
            st.write("Not available")

    st.divider()

    st.subheader("System Actions")

    action_cols = st.columns(3)
    with action_cols[0]:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    with action_cols[1]:
        if st.button("📖 API Docs", use_container_width=True):
            webbrowser.open_new_tab(f"{API_BASE_URL}/docs")

    with action_cols[2]:
        if st.button("🧹 Clear Cache", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['saved_searches', 'chat_history']:
                    del st.session_state[key]
            st.rerun()

def show_api_docs():
    """Show API documentation"""
    st.header("📖 API Documentation")

    st.markdown(f"""
    ### Backend API Endpoints
    
    Your backend is running at: `{API_BASE_URL}`
    
    #### Available Endpoints:
    
    1. **`GET /`** - Health check
       - Returns API status
    
    2. **`GET /stats`** - System statistics
       - Returns document and entity counts
    
    3. **`POST /search`** - Semantic search
       - Request: `{{"query": "search terms", "limit": 10}}`
       - Returns: Search results with relevance scores
    
    4. **`POST /ask`** - RAG question answering
       - Request: `{{"query": "your question", "use_openai": true}}`
       - Returns: AI answer with sources
    
    5. **`GET /entities`** - Entity retrieval
       - Parameters: `entity_type`, `limit`

       - Returns: Entities with counts
    
    6. **`GET /document/{'{id}'}`** - Document details
       - Returns: Full document with entities
    
    #### Testing the API:
    
    You can test the API directly:
    """)

    st.code("""
    # Test health check
    curl http://localhost:8000/
    
    # Test search
    curl -X POST http://localhost:8000/search \\
      -H "Content-Type: application/json" \\
      -d '{"query": "Zheng He", "limit": 5}'
    
    # Test RAG
    curl -X POST http://localhost:8000/ask \\
      -H "Content-Type: application/json" \\
      -d '{"query": "What evidence exists for Chinese exploration?", "use_openai": true}'
    """, language="bash")

    st.link_button("🔗 Open Interactive API Docs", f"{API_BASE_URL}/docs")

if __name__ == "__main__":
    main()
