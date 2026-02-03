"""
2_backend_api.py - COMPLETE Backend API with all endpoints
UPDATED: Includes /health, /timeline, /map, and other missing endpoints
"""

import os
import sys
import json
import sqlite3
import faiss
import pickle
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime
import re

# OpenAI imports - ADD YOUR API KEY HERE (Line 15-20)
from openai import OpenAI

# LINE 15-20: Add your OpenAI API key
client = OpenAI(
    api_key="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"  # ← YOUR KEY GOES HERE
)

# Initialize FastAPI app
app = FastAPI(
    title="1421 Research API",
    description="Complete API for 1421 research database",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
class ResearchBackend:
    def __init__(self):
        self.db_path = "knowledge_base.db"
        self.vector_dir = Path("vector_databases/main_index")

        # Load database
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        # Load vector database
        self.load_vector_database()

        # Load embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Backend initialized with all endpoints")

    def load_vector_database(self):
        """Load FAISS vector database"""
        try:
            index_file = self.vector_dir / "faiss_index.bin"
            metadata_file = self.vector_dir / "faiss_metadata.pkl"

            if not index_file.exists():
                raise FileNotFoundError("Vector database not found")

            self.index = faiss.read_index(str(index_file))

            with open(metadata_file, 'rb') as f:
                metadata = pickle.load(f)
                self.documents = metadata['documents']
                self.metadatas = metadata['metadatas']

            print(f"✅ Vector database loaded: {len(self.documents)} documents")

        except Exception as e:
            print(f"❌ Error loading vector database: {e}")
            self.index = None
            self.documents = []
            self.metadatas = []

    def semantic_search(self, query: str, k: int = 10, filters: Dict = None):
        """Perform semantic search with optional filters"""
        if not self.index:
            return []

        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype('float32')

        # Search
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadatas):
                # Get document from database for full details
                doc_id = self.metadatas[idx]['id']
                doc_details = self.get_document_details(doc_id)

                if doc_details:
                    # Apply filters if provided
                    if filters:
                        if filters.get('filter_source') and doc_details['source_type'] != filters['filter_source']:
                            continue
                        if filters.get('filter_year_min') or filters.get('filter_year_max'):
                            # Extract year from content
                            content = doc_details['content']
                            years = re.findall(r'\b(1[3-9]\d{2}|20[0-2]\d)\b', content)
                            if years:
                                year = int(years[0])
                                if filters.get('filter_year_min') and year < filters['filter_year_min']:
                                    continue
                                if filters.get('filter_year_max') and year > filters['filter_year_max']:
                                    continue

                    results.append({
                        'document_id': doc_id,
                        'title': doc_details['title'],
                        'author': doc_details['author'],
                        'source_type': doc_details['source_type'],
                        'url': doc_details['url'],
                        'word_count': doc_details['word_count'],
                        'snippet': doc_details['content'][:300] + "...",
                        'similarity': 1.0 / (1.0 + distances[0][i]),  # Convert distance to similarity
                        'distance': float(distances[0][i])
                    })

        return results

    def get_document_details(self, doc_id: int):
        """Get full document details"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT d.*, 
                   GROUP_CONCAT(e.entity_text || '|' || e.entity_type) as entities_str
            FROM documents d
            LEFT JOIN entities e ON d.id = e.doc_id
            WHERE d.id = ?
            GROUP BY d.id
        """, (doc_id,))

        row = cursor.fetchone()
        if row:
            doc = dict(row)

            # Parse entities
            entities = []
            if doc.get('entities_str'):
                for entity_str in doc['entities_str'].split(','):
                    if '|' in entity_str:
                        text, entity_type = entity_str.split('|', 1)
                        entities.append({
                            'text': text.strip(),
                            'type': entity_type.strip()
                        })
            doc['entities'] = entities

            # Remove raw string
            if 'entities_str' in doc:
                del doc['entities_str']

            return doc
        return None

    def rag_query(self, query: str, include_sources: bool = True, use_openai: bool = True):
        """RAG query with OpenAI"""
        # Step 1: Semantic search
        search_results = self.semantic_search(query, k=5)

        if not search_results:
            return {
                "answer": "No relevant documents found in the database.",
                "sources": [],
                "confidence": 0.0
            }

        # Step 2: Prepare context
        context_parts = []
        for result in search_results:
            doc_details = self.get_document_details(result['document_id'])
            if doc_details:
                context_parts.append(f"[Source: {doc_details['title']}]\n{doc_details['content'][:1000]}")

        context = "\n\n".join(context_parts)

        if use_openai:
            # Step 3: Query OpenAI with RAG context
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a historian specializing in Chinese exploration history. 
                            Answer questions based ONLY on the provided context. 
                            Cite your sources using the [Source: ...] format.
                            If you cannot answer based on the context, say so."""
                        },
                        {
                            "role": "user",
                            "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer based on the context above:"
                        }
                    ],
                    max_tokens=500,
                    temperature=0.7
                )

                answer = response.choices[0].message.content
                confidence = min(0.9, 0.5 + (len(search_results) / 10))  # Simple confidence calculation

            except Exception as e:
                print(f"OpenAI error: {e}")
                # Fallback to simple context return
                return self.fallback_rag(query, context, search_results)
        else:
            return self.fallback_rag(query, context, search_results)

        # Prepare sources
        sources = []
        if include_sources:
            for result in search_results[:3]:  # Limit to top 3 sources
                doc_details = self.get_document_details(result['document_id'])
                if doc_details:
                    sources.append({
                        'id': result['document_id'],
                        'title': doc_details['title'],
                        'author': doc_details['author'],
                        'source_type': doc_details['source_type'],
                        'url': doc_details['url']
                    })

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence
        }

    def fallback_rag(self, query: str, context: str, search_results: List):
        """Fallback RAG without OpenAI"""
        # Simple answer based on context
        answer = f"I found {len(search_results)} relevant documents about '{query}'. "
        answer += "The most relevant document is: "
        answer += f"'{search_results[0]['title']}' by {search_results[0]['author']}.\n\n"
        answer += f"Excerpt: {search_results[0]['snippet']}"

        sources = []
        for result in search_results[:3]:
            sources.append({
                'id': result['document_id'],
                'title': result['title'],
                'author': result['author'],
                'source_type': result['source_type'],
                'url': result['url']
            })

        return {
            "answer": answer,
            "sources": sources,
            "confidence": 0.5
        }

    def get_entities_data(self, entity_type: str = None, limit: int = 50):
        """Get entities from database"""
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
        entities = [dict(row) for row in rows]

        # Calculate totals by type
        by_type = {}
        for entity in entities:
            etype = entity['entity_type']
            by_type[etype] = by_type.get(etype, 0) + entity['count']

        return {
            "entities": entities,
            "total": len(entities),
            "by_type": by_type
        }

    def get_timeline_events(self, start_year: int = None, end_year: int = None):
        """Get timeline events from documents"""
        cursor = self.conn.cursor()

        # Get documents with years
        cursor.execute("SELECT id, title, content, source_type, url FROM documents")
        rows = cursor.fetchall()

        events = []
        for row in rows:
            doc_id, title, content, source_type, url = row

            # Extract years from content
            years = re.findall(r'\b(1[3-9]\d{2})\b', content)

            for year in years[:3]:  # Limit to 3 years per document
                year_int = int(year)

                # Apply year filters
                if start_year and year_int < start_year:
                    continue
                if end_year and year_int > end_year:
                    continue

                # Get context around the year
                year_pos = content.find(year)
                start_pos = max(0, year_pos - 100)
                end_pos = min(len(content), year_pos + 200)
                context = content[start_pos:end_pos].strip()

                events.append({
                    'id': f"{doc_id}_{year}",
                    'date': year,
                    'description': title[:100],
                    'type': source_type or 'document',
                    'location': 'Unknown',  # Could extract from entities
                    'context': context,
                    'document_id': doc_id,
                    'document_title': title,
                    'document_url': url
                })

        # Sort by year
        events.sort(key=lambda x: int(x['date']))

        return {
            "events": events[:100],  # Limit to 100 events
            "total": len(events),
            "start_year": start_year,
            "end_year": end_year
        }

    def get_map_locations(self):
        """Get geographical locations from documents"""
        cursor = self.conn.cursor()

        # Get location entities
        cursor.execute("""
            SELECT entity_text, COUNT(*) as mention_count
            FROM entities 
            WHERE entity_type = 'LOCATION'
            GROUP BY entity_text
            ORDER BY mention_count DESC
            LIMIT 50
        """)

        rows = cursor.fetchall()

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
            'Peru': (-9.1900, -75.0152),
            'Mexico': (23.6345, -102.5528),
            'Pacific Ocean': (0, -160),
            'Indian Ocean': (-20, 80),
            'South China Sea': (12, 115),
            'Malacca': (2.1896, 102.2501),
            'Calicut': (11.2588, 75.7804),
            'Hormuz': (27.1561, 56.2815),
            'Mombasa': (-4.0435, 39.6682),
            'Zanzibar': (-6.1659, 39.2026),
            'Aden': (12.7855, 45.0187),
            'Quanzhou': (24.9139, 118.5858),
            'Guangzhou': (23.1291, 113.2644)
        }

        locations = []
        for row in rows:
            location_name, mention_count = row
            location_name_str = location_name if isinstance(location_name, str) else str(location_name)

            # Get coordinates
            coords = location_coords.get(location_name_str, None)
            if coords:
                latitude, longitude = coords

                # Determine location type
                if 'Ocean' in location_name_str or 'Sea' in location_name_str:
                    location_type = 'water'
                elif any(term in location_name_str for term in ['China', 'India', 'Africa', 'America']):
                    location_type = 'continent'
                else:
                    location_type = 'city'

                locations.append({
                    'name': location_name_str,
                    'latitude': latitude,
                    'longitude': longitude,
                    'type': location_type,
                    'mention_count': mention_count
                })

        return {
            "locations": locations,
            "total": len(locations)
        }

    def get_database_stats(self):
        """Get database statistics"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]

        cursor.execute("SELECT source_type, COUNT(*) FROM documents GROUP BY source_type")
        docs_by_source = dict(cursor.fetchall())

        cursor.execute("SELECT COUNT(*) FROM entities")
        total_entities = cursor.fetchone()[0]

        cursor.execute("SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type")
        entities_by_type = dict(cursor.fetchall())

        # Check RAG system
        rag_ready = self.index is not None and len(self.documents) > 0

        return {
            "documents": {
                "total": total_docs,
                "by_source": docs_by_source
            },
            "entities": {
                "total": total_entities,
                "by_type": entities_by_type
            },
            "rag_system": {
                "ready": rag_ready,
                "documents_indexed": len(self.documents) if self.documents else 0
            },
            "api": {
                "version": "1.0.0",
                "endpoints": 8
            }
        }

# Initialize backend
backend = ResearchBackend()

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    use_openai: bool = True

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    filters: Optional[Dict] = None

class QuestionRequest(BaseModel):
    question: str
    include_sources: bool = True

# API endpoints
@app.get("/")
async def read_root():
    return {"message": "1421 Research API", "status": "online", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": backend.db_path,
        "vector_docs": len(backend.documents) if backend.documents else 0
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return backend.get_database_stats()

@app.post("/search")
async def semantic_search(request: SearchRequest):
    """Semantic document search"""
    results = backend.semantic_search(
        query=request.query,
        k=request.top_k,
        filters=request.filters
    )
    return {"query": request.query, "results": results, "count": len(results)}

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask question via RAG"""
    response = backend.rag_query(
        query=request.question,
        include_sources=request.include_sources,
        use_openai=True  # Always use OpenAI for better answers
    )
    return response

@app.get("/entities")
async def get_entities(entity_type: Optional[str] = None, limit: int = 50):
    """Get entities"""
    return backend.get_entities_data(entity_type=entity_type, limit=limit)

@app.get("/timeline")
async def get_timeline(start_year: Optional[int] = None, end_year: Optional[int] = None):
    """Get timeline events"""
    return backend.get_timeline_events(start_year=start_year, end_year=end_year)

@app.get("/map")
async def get_map_data():
    """Get geographical data for map"""
    return backend.get_map_locations()

@app.get("/document/{doc_id}")
async def get_document(doc_id: int):
    """Get document details by ID"""
    doc = backend.get_document_details(doc_id)
    if doc:
        return doc
    raise HTTPException(status_code=404, detail="Document not found")

@app.get("/docs")
async def get_api_docs():
    """Redirect to OpenAPI docs"""
    return {"message": "OpenAPI documentation available at /docs"}

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Starting 1421 Research API server...")
    print(f"📚 API Documentation available at: http://localhost:8000/docs")
    print(f"🏠 Health check: http://localhost:8000/health")
    print(f"📊 Stats: http://localhost:8000/stats")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8000)
