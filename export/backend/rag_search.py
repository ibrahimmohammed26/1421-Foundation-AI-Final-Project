import os
import pickle
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document as LangChainDocument
from langchain import RecursiveCharacterTextSplitter
from langchain import RetrievalQA
from langchain import ContextualCompressionRetriever
from langchain import LLMChainExtractor

class HybridDocumentSearch:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7
        )
        
        # Load vector database
        self.index_path = Path("data/vector_databases/main_index/faiss_index.bin")
        self.metadata_path = Path("data/vector_databases/main_index/faiss_metadata.pkl")
        self.db_path = Path("data/knowledge_base.db")
        
        self.index = None
        self.metadata = None
        self.load_vector_db()
        
    def load_vector_db(self):
        """Load FAISS index and metadata."""
        if self.index_path.exists() and self.metadata_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            print(f"✓ Loaded FAISS index with {self.index.ntotal} vectors")
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search documents using vector similarity."""
        if not self.index or not self.metadata:
            return []
        
        # Get query embedding
        query_embedding = self.embeddings.embed_query(query)
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search in FAISS
        distances, indices = self.index.search(query_vector, top_k)
        
        # Get metadata for results
        results = []
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and str(idx) in self.metadata:
                doc_id = self.metadata[str(idx)].get('id', str(idx))
                cursor.execute("""
                    SELECT id, title, author, year, type, description, tags, 
                           content_preview, source_file, page_number
                    FROM documents WHERE id = ?
                """, (doc_id,))
                row = cursor.fetchone()
                if row:
                    results.append({
                        'id': row['id'],
                        'title': row['title'],
                        'author': row['author'],
                        'year': row['year'],
                        'type': row['type'],
                        'description': row['description'],
                        'tags': row['tags'].split(',') if row['tags'] else [],
                        'content_preview': row['content_preview'],
                        'source_file': row['source_file'],
                        'page_number': row['page_number'],
                        'similarity_score': float(distances[0][i])
                    })
        
        conn.close()
        return results
    
    def get_relevant_context(self, query: str, top_k: int = 3) -> str:
        """Get relevant document context for RAG."""
        docs = self.search_documents(query, top_k)
        if not docs:
            return ""
        
        context = "Relevant documents from the knowledge base:\n\n"
        for i, doc in enumerate(docs, 1):
            context += f"[Document {i}] {doc['title']} ({doc['year']}) by {doc['author']}\n"
            context += f"Type: {doc['type']}\n"
            context += f"Content: {doc['content_preview']}\n"
            context += f"Tags: {', '.join(doc['tags'])}\n\n"
        
        return context
    
    def hybrid_search_prompt(self, user_query: str) -> str:
        """Create a prompt that combines web knowledge and document search."""
        doc_context = self.get_relevant_context(user_query)
        
        base_prompt = """You are a professional historian specialising in Chinese maritime exploration 
during the Ming dynasty (1368–1644), particularly the voyages of Admiral Zheng He and the 
controversial 1421 hypothesis by Gavin Menzies.

{context}

Using both your general knowledge and the provided document excerpts above, answer the following question:

{query}

Provide a comprehensive, well-structured answer in clear, academic UK English. Cite the documents when relevant.
"""
        
        return base_prompt.format(
            context=doc_context if doc_context else "(No specific documents found - using general knowledge only)",
            query=user_query
        )

# Global instance
_hybrid_search = None

def get_hybrid_search():
    global _hybrid_search
    if _hybrid_search is None:
        _hybrid_search = HybridDocumentSearch()
    return _hybrid_search