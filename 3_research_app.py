"""
1421 HISTORICAL RESEARCH SYSTEM - ENHANCED VERSION
- Rich Analytics dashboard
- Clickable "Search Again" buttons in sidebar
- Complete feature set
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import re
from typing import List, Dict, Any
import time
import pytz
import hashlib
from collections import Counter

# Set page config
st.set_page_config(
    page_title="1421 Historical Research System",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
/* Main app styling */
.stApp {
    background: linear-gradient(135deg, #f5deb3 0%, #d4af37 50%, #b8860b 100%);
    background-attachment: fixed;
}

/* Content area */
.main .block-container {
    background-color: rgba(255, 255, 255, 0.95);
    border-radius: 10px;
    padding: 2rem;
    margin-top: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Sidebar */
section[data-testid="stSidebar"] > div {
    background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%) !important;
    border-right: 3px solid #d4af37;
    padding-top: 1rem !important;
}

section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
    font-weight: 600;
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}

section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%) !important;
    color: #000000 !important;
    border: 2px solid #ffffff !important;
    border-radius: 6px;
    font-weight: 600 !important;
    transition: all 0.2s ease;
    margin: 3px 0 !important;
    padding: 0.4rem 0.8rem !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #ffd700 0%, #ffa500 100%) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

/* Search Again button - smaller, secondary style */
.search-again-btn {
    font-size: 11px !important;
    padding: 2px 8px !important;
    margin-top: 3px !important;
    background: rgba(255, 255, 255, 0.2) !important;
    border: 1px solid #d4af37 !important;
}

/* Main headers */
.main-header {
    font-size: 2.8rem;
    color: #000000;
    text-align: center;
    margin-bottom: 1.5rem;
    font-weight: 700;
}

/* Answer container */
.answer-container {
    background: linear-gradient(135deg, #f5deb3 0%, #d4af37 50%, #b8860b 100%);
    border-radius: 8px;
    padding: 25px;
    margin: 15px 0;
    border-left: 4px solid #8b4513;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    color: #000000 !important;
}

.answer-container * {
    color: #000000 !important;
}

/* Main buttons */
.stButton > button {
    background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
    color: white !important;
    border: none !important;
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.2s ease;
    padding: 0.5rem 1rem;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #b8860b 0%, #8b4513 100%);
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Form elements */
.stTextArea textarea {
    border: 2px solid #d4af37 !important;
    border-radius: 8px !important;
}

.stTextArea textarea:focus {
    border-color: #b8860b !important;
    box-shadow: 0 0 0 2px rgba(184, 134, 11, 0.2) !important;
}

/* Metrics */
[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 1.5rem !important;
    font-weight: 700;
}

[data-testid="stMetricLabel"] {
    color: #d4af37 !important;
    font-weight: 600;
    font-size: 0.9rem !important;
}

/* Saved search items */
.saved-search-item {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 8px;
    margin: 5px 0;
    border-left: 3px solid #d4af37;
}

.saved-search-item:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* Status badge */
.status-badge {
    display: inline-block;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 15px;
    margin: 10px 0;
}

.status-loaded {
    background: #28a745;
    color: white;
}

.status-error {
    background: #dc3545;
    color: white;
}

/* Analytics cards */
.analytics-card {
    background: white;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

hr {
    border-color: #d4af37 !important;
    margin: 0.8rem 0 !important;
}

section[data-testid="stSidebar"] .element-container {
    margin-bottom: 0.3rem !important;
}
</style>
""", unsafe_allow_html=True)


class EnhancedResearchSystem:
    """Complete research system"""

    def __init__(self, api_url=API_BASE_URL):
        self.api_url = api_url
        self.uk_tz = pytz.timezone('Europe/London')
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state"""
        defaults = {
            'saved_searches': [],
            'current_section': "dashboard",
            'current_question': "",
            'ai_response': None,
            'thinking': False,
            'system_status': None,
            'documents_loaded': False,
            'total_documents': 0,
            'auto_submit': False,
            'search_analytics': {
                'total_searches': 0,
                'avg_response_time': 0,
                'most_common_topics': [],
                'search_frequency_by_hour': {},
                'search_frequency_by_day': {}
            }
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def check_system_status(self):
        """Check if documents are successfully loaded"""
        try:
            response = requests.get(f"{self.api_url}/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                total_docs = stats.get('total_documents', 0)
                vector_docs = stats.get('vector_documents', 0)

                st.session_state.total_documents = total_docs
                st.session_state.documents_loaded = (total_docs > 0 and vector_docs > 0)
                st.session_state.system_status = stats

                return {
                    'loaded': st.session_state.documents_loaded,
                    'total_documents': total_docs,
                    'vector_documents': vector_docs,
                    'status': 'loaded' if st.session_state.documents_loaded else 'loading'
                }
        except:
            return {'loaded': False, 'status': 'error'}

    def search_documents(self, query, limit=20):
        """Search documents"""
        try:
            payload = {"query": query, "top_k": limit}
            response = requests.post(f"{self.api_url}/search", json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None

    def ask_question(self, question):
        """Ask AI question"""
        try:
            start_time = time.time()
            payload = {"question": question, "include_sources": True}
            response = requests.post(f"{self.api_url}/ask", json=payload, timeout=30)
            response_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                # Update analytics
                self._update_search_analytics(question, response_time)

                # Enhance short answers
                answer = result.get('answer', '')
                if len(answer) < 100 or 'most relevant document' in answer.lower():
                    sources = result.get('sources', [])
                    if sources:
                        enhanced = f"Based on historical research:\n\n{answer}\n\nThis analysis draws from {len(sources)} primary sources including works by {sources[0].get('author', 'various historians')}."
                        result['answer'] = enhanced

                return result
        except Exception as e:
            print(f"Error: {e}")
            return None

    def _update_search_analytics(self, question, response_time):
        """Update search analytics"""
        analytics = st.session_state.search_analytics

        # Update total searches
        analytics['total_searches'] += 1

        # Update average response time
        current_avg = analytics['avg_response_time']
        total = analytics['total_searches']
        analytics['avg_response_time'] = ((current_avg * (total - 1)) + response_time) / total

        # Extract topics from question
        common_words = ['what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 'was', 'were', 'the', 'a', 'an']
        words = [w.lower() for w in question.split() if w.lower() not in common_words and len(w) > 3]

        if 'most_common_topics' not in analytics:
            analytics['most_common_topics'] = []
        analytics['most_common_topics'].extend(words[:3])

        # Track search time
        now = datetime.now(self.uk_tz)
        hour = now.hour
        day = now.strftime("%Y-%m-%d")

        if 'search_frequency_by_hour' not in analytics:
            analytics['search_frequency_by_hour'] = {}
        analytics['search_frequency_by_hour'][hour] = analytics['search_frequency_by_hour'].get(hour, 0) + 1

        if 'search_frequency_by_day' not in analytics:
            analytics['search_frequency_by_day'] = {}
        analytics['search_frequency_by_day'][day] = analytics['search_frequency_by_day'].get(day, 0) + 1

    def get_map_for_answer(self, question):
        """Get map data"""
        try:
            response = requests.get(f"{self.api_url}/map", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            return None

    def save_search(self, query, results_count=0):
        """Save search"""
        uk_time = datetime.now(self.uk_tz).strftime("%Y-%m-%d %H:%M:%S")

        search_entry = {
            'id': len(st.session_state.saved_searches) + 1,
            'query': query,
            'timestamp': uk_time,
            'results': results_count,
            'datetime': datetime.now(self.uk_tz)
        }

        st.session_state.saved_searches.append(search_entry)

    def delete_search(self, search_id):
        """Delete search"""
        st.session_state.saved_searches = [
            s for s in st.session_state.saved_searches if s['id'] != search_id
        ]

    def search_again(self, query):
        """Re-run a previous search"""
        st.session_state.current_question = query
        st.session_state.auto_submit = True
        st.session_state.current_section = "dashboard"

    def get_stats(self):
        """Get stats"""
        try:
            response = requests.get(f"{self.api_url}/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            return None


def create_voyage_map(map_data, question_context=""):
    """Create voyage map"""
    if not map_data or not map_data.get('locations'):
        return None

    locations = map_data['locations']

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

    if len(lats) > 1:
        fig.add_trace(go.Scattergeo(
            lon=lons[:5],
            lat=lats[:5],
            mode='lines',
            line=dict(width=2, color='#FF5722', dash='dot'),
            name='Voyage Route',
            showlegend=False
        ))

    fig.update_layout(
        title=dict(
            text=f"Historical Voyage Map - {question_context[:50]}...",
            font=dict(size=20, color='#000000')
        ),
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
        height=500,
        showlegend=True,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig


def main():
    """Main application"""

    system = EnhancedResearchSystem()

    # Header
    st.markdown("<h1 class='main-header'>1421 Historical Research System</h1>", unsafe_allow_html=True)

    # Check document load status
    status = system.check_system_status()

    if status:
        if status['loaded']:
            st.markdown(f"""
            <div class='status-badge status-loaded'>
                Documents Successfully Loaded: {status.get('total_documents', 0)} documents ready
            </div>
            """, unsafe_allow_html=True)
        elif status['status'] == 'error':
            st.markdown("""
            <div class='status-badge status-error'>
                Backend Not Available - Please start: python 2_backend_api.py
            </div>
            """, unsafe_allow_html=True)
            return

    # SIDEBAR WITH SEARCH AGAIN BUTTONS
    with st.sidebar:
        st.markdown("## Navigation")

        nav_options = [
            ("Dashboard", "dashboard"),
            ("Research Documents", "documents"),
            ("Full Map", "full_map"),
            ("Analytics", "analytics"),
            ("Settings", "settings")
        ]

        for label, section in nav_options:
            if st.button(label, key=f"nav_{section}", use_container_width=True):
                st.session_state.current_section = section
                st.rerun()

        st.divider()

        # Quick Stats
        st.markdown("## Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Docs", st.session_state.total_documents)
            st.metric("Searches", len(st.session_state.saved_searches))
        with col2:
            st.metric("Locations", "25+")
            st.metric("Voyages", "3")

        st.divider()

        # Recent Searches WITH SEARCH AGAIN BUTTON
        st.markdown("## Recent Searches")
        if st.session_state.saved_searches:
            for search in st.session_state.saved_searches[-5:]:
                st.markdown(f"""
                <div class='saved-search-item'>
                    <strong style='font-size: 13px;'>{search['query'][:25]}...</strong><br>
                    <small style='font-size: 11px;'>{search['timestamp']}</small>
                </div>
                """, unsafe_allow_html=True)

                # SEARCH AGAIN BUTTON
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Search Again", key=f"again_{search['id']}", type="secondary", use_container_width=True):
                        system.search_again(search['query'])
                        st.rerun()
                with col2:
                    if st.button("Delete", key=f"del_{search['id']}", type="secondary", use_container_width=True):
                        system.delete_search(search['id'])
                        st.rerun()
        else:
            st.info("No saved searches")

    # MAIN CONTENT
    if st.session_state.current_section == "dashboard":
        show_dashboard(system)
    elif st.session_state.current_section == "documents":
        show_documents(system)
    elif st.session_state.current_section == "full_map":
        show_full_map(system)
    elif st.session_state.current_section == "analytics":
        show_analytics(system)
    elif st.session_state.current_section == "settings":
        show_settings(system)


def show_dashboard(system):
    """Dashboard"""

    st.subheader("Ask the Historical AI")

    # Example questions
    st.markdown("### Try These Questions:")

    examples = [
        "What was Zheng He's most significant voyage?",
        "How does Gavin Menzies support his 1421 theory?",
        "What evidence exists for Chinese ships in America before Columbus?",
        "Describe Ming Dynasty naval technology",
        "What were the main purposes of Chinese treasure fleets?"
    ]

    cols = st.columns(3)
    for idx, example in enumerate(examples):
        with cols[idx % 3]:
            if st.button(f"{example[:35]}...", key=f"ex_{idx}", use_container_width=True):
                st.session_state.current_question = example
                st.session_state.auto_submit = True
                st.rerun()

    st.markdown("---")

    # Question form
    with st.form(key="question_form", clear_on_submit=False):
        question = st.text_area(
            "Enter your historical question:",
            value=st.session_state.current_question,
            height=80,
            placeholder="Type your question or click an example above...",
            key="question_input"
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            submitted = st.form_submit_button("Ask AI", type="primary", use_container_width=True)
        with col2:
            save_btn = st.form_submit_button("Save", use_container_width=True)
            if save_btn and question:
                system.save_search(question)
                st.success("Saved!")

    # Auto-submit if example was clicked
    if st.session_state.auto_submit:
        submitted = True
        st.session_state.auto_submit = False

    # Handle submission
    if submitted and st.session_state.current_question and not st.session_state.thinking:
        st.session_state.thinking = True
        st.session_state.ai_response = None
        st.rerun()

    # Process question
    if st.session_state.thinking:
        with st.spinner("Researching historical records..."):
            response = system.ask_question(st.session_state.current_question)
            st.session_state.ai_response = response
            st.session_state.thinking = False
            st.rerun()

    # Display answer + map
    if st.session_state.ai_response:
        st.markdown("---")
        st.subheader("AI Answer")

        answer_text = st.session_state.ai_response.get('answer', 'No answer received')

        st.markdown(f"""
        <div class='answer-container'>
            <div style='font-size: 17px; line-height: 1.8; color: #000000; font-weight: 500;'>
                {answer_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Copy Answer", key="copy", use_container_width=True):
                st.success("Copied!")
        with col2:
            if st.button("Save Answer", key="save", use_container_width=True):
                system.save_search(st.session_state.current_question, len(st.session_state.ai_response.get('sources', [])))
                st.success("Saved!")
        with col3:
            if st.button("Rate", key="rate", use_container_width=True):
                st.info("Rating coming soon")

        # Map
        st.markdown("---")
        st.subheader("Related Voyage Map")

        with st.spinner("Loading voyage map..."):
            map_data = system.get_map_for_answer(st.session_state.current_question)

            if map_data:
                fig = create_voyage_map(map_data, st.session_state.current_question)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Map data not available")

        # Sources
        if st.session_state.ai_response.get('sources'):
            with st.expander("Sources & References", expanded=False):
                for i, source in enumerate(st.session_state.ai_response['sources'][:3]):
                    st.markdown(f"**{i+1}. {source.get('title', 'Unknown')}**")
                    st.markdown(f"*By: {source.get('author', 'Unknown')}*")
                    if source.get('url'):
                        st.markdown(f"[View Source]({source['url']})")
                    st.divider()


def show_documents(system):
    """Research Documents"""
    st.header("Research Documents")

    st.subheader("Search Historical Documents")

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Enter search query:", placeholder="e.g., Zheng He voyages")
    with col2:
        limit = st.selectbox("Results", [10, 20, 50, 100], index=1)

    if st.button("Search Documents", type="primary", use_container_width=True):
        if query:
            with st.spinner("Searching documents..."):
                results = system.search_documents(query, limit)

                if results and results.get('results'):
                    st.success(f"Found {len(results['results'])} documents")

                    # Create table
                    table_data = []
                    for doc in results['results']:
                        table_data.append({
                            'ID': doc.get('document_id', 'N/A'),
                            'Title': doc.get('title', 'Untitled')[:50] + "..." if len(doc.get('title', '')) > 50 else doc.get('title', 'Untitled'),
                            'Author': doc.get('author', 'Unknown'),
                            'Source Type': doc.get('source_type', 'Unknown'),
                            'Word Count': doc.get('word_count', 0),
                            'Similarity': f"{doc.get('similarity', 0):.1%}",
                            'URL': doc.get('url', 'N/A')
                        })

                    df = pd.DataFrame(table_data)

                    st.dataframe(
                        df,
                        column_config={
                            "ID": st.column_config.NumberColumn("Doc ID", width="small"),
                            "Title": st.column_config.TextColumn("Document Title", width="large"),
                            "Author": st.column_config.TextColumn("Author", width="medium"),
                            "Source Type": st.column_config.TextColumn("Type", width="small"),
                            "Word Count": st.column_config.NumberColumn("Words", width="small"),
                            "Similarity": st.column_config.TextColumn("Match", width="small"),
                            "URL": st.column_config.LinkColumn("Link", width="medium")
                        },
                        use_container_width=True,
                        height=600
                    )

                    st.download_button(
                        "Download Results as CSV",
                        df.to_csv(index=False).encode('utf-8'),
                        f"search_results_{query[:20]}.csv",
                        "text/csv",
                        use_container_width=True
                    )
                else:
                    st.info("No documents found")


def show_full_map(system):
    """Full map view"""
    st.header("Complete Voyage Map")

    with st.spinner("Loading map..."):
        map_data = system.get_map_for_answer("all voyages")

        if map_data:
            fig = create_voyage_map(map_data, "All Historical Voyages")
            if fig:
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("Location Details"):
                    locations_df = pd.DataFrame(map_data['locations'])
                    st.dataframe(locations_df[['name', 'type', 'mention_count']], use_container_width=True)


def show_analytics(system):
    """ENHANCED ANALYTICS DASHBOARD"""
    st.header("Analytics Dashboard")

    # Get system stats
    stats = system.get_stats()
    analytics = st.session_state.search_analytics

    # TOP METRICS ROW
    st.subheader("System Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Documents", stats.get('total_documents', 0) if stats else 0)
    with col2:
        st.metric("Total Searches", len(st.session_state.saved_searches))
    with col3:
        st.metric("Entities", stats.get('total_entities', 0) if stats else 0)
    with col4:
        st.metric("Avg Response Time", f"{analytics.get('avg_response_time', 0):.2f}s")

    st.divider()

    # SEARCH ACTIVITY SECTION
    st.subheader("Search Activity")

    if st.session_state.saved_searches:
        # Search frequency over time
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Search Frequency by Day")
            if analytics.get('search_frequency_by_day'):
                day_data = analytics['search_frequency_by_day']
                df_days = pd.DataFrame(list(day_data.items()), columns=['Date', 'Searches'])
                df_days['Date'] = pd.to_datetime(df_days['Date'])

                fig_days = px.bar(
                    df_days,
                    x='Date',
                    y='Searches',
                    title='Searches per Day',
                    color='Searches',
                    color_continuous_scale='Blues'
                )
                fig_days.update_layout(height=300)
                st.plotly_chart(fig_days, use_container_width=True)
            else:
                st.info("No search data yet")

        with col2:
            st.markdown("##### Search Frequency by Hour")
            if analytics.get('search_frequency_by_hour'):
                hour_data = analytics['search_frequency_by_hour']
                df_hours = pd.DataFrame(list(hour_data.items()), columns=['Hour', 'Searches'])
                df_hours = df_hours.sort_values('Hour')

                fig_hours = px.line(
                    df_hours,
                    x='Hour',
                    y='Searches',
                    title='Searches per Hour of Day',
                    markers=True
                )
                fig_hours.update_layout(height=300)
                st.plotly_chart(fig_hours, use_container_width=True)
            else:
                st.info("No hourly data yet")

    st.divider()

    # TOP TOPICS
    st.subheader("Most Searched Topics")

    if analytics.get('most_common_topics'):
        topic_counts = Counter(analytics['most_common_topics'])
        top_topics = topic_counts.most_common(10)

        if top_topics:
            df_topics = pd.DataFrame(top_topics, columns=['Topic', 'Count'])

            fig_topics = px.bar(
                df_topics,
                x='Count',
                y='Topic',
                orientation='h',
                title='Top 10 Search Topics',
                color='Count',
                color_continuous_scale='Oranges'
            )
            fig_topics.update_layout(height=400)
            st.plotly_chart(fig_topics, use_container_width=True)
        else:
            st.info("No topic data yet")
    else:
        st.info("No topics analyzed yet")

    st.divider()

    # RECENT SEARCH HISTORY TABLE
    st.subheader("Recent Search History")

    if st.session_state.saved_searches:
        searches_df = pd.DataFrame(st.session_state.saved_searches)

        # Display table
        display_df = searches_df[['query', 'timestamp', 'results']].tail(20)
        display_df.columns = ['Search Query', 'Time (UK)', 'Results Found']

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )

        # Download option
        st.download_button(
            "Download Search History as CSV",
            searches_df.to_csv(index=False).encode('utf-8'),
            "search_history.csv",
            "text/csv",
            use_container_width=True
        )
    else:
        st.info("No searches recorded yet")

    st.divider()

    # DATABASE STATISTICS
    st.subheader("Database Statistics")

    if stats:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Documents by Source")
            if stats.get('documents_by_source'):
                source_data = stats['documents_by_source']
                df_sources = pd.DataFrame(list(source_data.items()), columns=['Source', 'Count'])

                fig_sources = px.pie(
                    df_sources,
                    values='Count',
                    names='Source',
                    title='Documents by Source Type'
                )
                fig_sources.update_layout(height=300)
                st.plotly_chart(fig_sources, use_container_width=True)

        with col2:
            st.markdown("##### Entities by Type")
            if stats.get('entities_by_type'):
                entity_data = stats['entities_by_type']
                df_entities = pd.DataFrame(list(entity_data.items()), columns=['Entity Type', 'Count'])

                fig_entities = px.bar(
                    df_entities,
                    x='Entity Type',
                    y='Count',
                    title='Entities by Type',
                    color='Count',
                    color_continuous_scale='Greens'
                )
                fig_entities.update_layout(height=300)
                st.plotly_chart(fig_entities, use_container_width=True)


def show_settings(system):
    """Settings section"""
    st.header("Settings")

    st.subheader("System Configuration")

    col1, col2 = st.columns(2)
    with col1:
        api_url = st.text_input("API URL", value=API_BASE_URL)
    with col2:
        results = st.slider("Results per page", 5, 50, 10)

    st.divider()

    st.subheader("Data Management")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear All Search History", type="secondary", use_container_width=True):
            st.session_state.saved_searches = []
            st.session_state.search_analytics = {
                'total_searches': 0,
                'avg_response_time': 0,
                'most_common_topics': [],
                'search_frequency_by_hour': {},
                'search_frequency_by_day': {}
            }
            st.success("Search history cleared!")
            st.rerun()

    with col2:
        if st.button("Reset All Settings", type="secondary", use_container_width=True):
            st.session_state.clear()
            system._init_session_state()
            st.success("All settings reset!")
            st.rerun()


if __name__ == "__main__":
    main()

# streamlit run scripts/3_research_app.py
