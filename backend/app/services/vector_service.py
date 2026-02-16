import os
import pickle
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import faiss
import openai
from app.config import settings

class FAISSService:
    """Vector search service using FAISS index"""
    
    def __init__(self, index_path: Optional[str] = None):
        """
        Initialize FAISS vector service
        
        Args:
            index_path: Path to directory containing FAISS files
        """
        if index_path is None:
            # Look for vector_databases folder
            possible_paths = [
                Path("data/vector_databases"),
                Path("./data/vector_databases"),
                Path(__file__).parent.parent.parent / "data" / "vector_databases",
            ]
            
            for p in possible_paths:
                if p.exists():
                    index_path = str(p)
                    print(f"Found vector database at: {index_path}")
                    break
        
        if not index_path:
            raise FileNotFoundError(
                "Could not find vector database folder. "
                "Please set VECTOR_DB_PATH in .env"
            )
        
        self.index_path = Path(index_path)
        self.index = None
        self.metadata = None
        self.stats = None
        self.dimension = None
        
        # Load FAISS index and metadata
        self._load_index()
    
    def _load_index(self):
        """Load FAISS index and associated files"""
        try:
            # Load FAISS index
            index_file = self.index_path / "faiss_index.bin"
            if index_file.exists():
                self.index = faiss.read_index(str(index_file))
                self.dimension = self.index.d
                print(f"Loaded FAISS index with dimension: {self.dimension}")
            else:
                raise FileNotFoundError(f"FAISS index not found at {index_file}")
            
            # Load metadata
            metadata_file = self.index_path / "faiss_metadata.pkl"
            if metadata_file.exists():
                with open(metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                print(f"Loaded metadata for {len(self.metadata)} documents")
            
            # Load stats
            stats_file = self.index_path / "database_stats.json"
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    self.stats = json.load(f)
                print(f"Loaded stats: {self.stats}")
                
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            raise
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get OpenAI embedding for query text
        
        You need the same embedding model that was used to create the index!
        Typically 'text-embedding-ada-002' or 'text-embedding-3-small'
        """
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",  # Adjust based on your index
                input=text
            )
            embedding = response['data'][0]['embedding']
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            print(f"Error getting embedding: {e}")
            # Return random vector as fallback (not ideal)
            return np.random.randn(self.dimension).astype(np.float32)
    
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar documents using FAISS
        
        Args:
            query: Search query text
            k: Number of results to return
            
        Returns:
            List of documents with similarity scores
        """
        if self.index is None or self.metadata is None:
            print("FAISS index not loaded")
            return []
        
        try:
            # Convert query to embedding
            query_vector = self.get_embedding(query)
            
            # Reshape for FAISS (needs 2D array)
            query_vector = query_vector.reshape(1, -1)
            
            # Search
            scores, indices = self.index.search(query_vector, k)
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= 0 and idx < len(self.metadata):  # Valid index
                    doc = self.metadata[idx]
                    
                    # Convert score to similarity (FAISS returns L2 distance)
                    # Lower distance = more similar
                    similarity = 1 / (1 + score)  # Convert to 0-1 scale
                    
                    results.append({
                        'id': idx,
                        'title': doc.get('title', 'Unknown'),
                        'content': doc.get('content', '')[:500] + '...' if len(doc.get('content', '')) > 500 else doc.get('content', ''),
                        'author': doc.get('author', 'Unknown'),
                        'year': doc.get('year', 'Unknown'),
                        'source': doc.get('source', 'Document'),
                        'similarity_score': float(similarity),
                        'distance': float(score)
                    })
            
            return results
            
        except Exception as e:
            print(f"Error during FAISS search: {e}")
            return []
    
    def search_by_vector(self, vector: np.ndarray, k: int = 10) -> List[Dict]:
        """Search using a pre-computed vector"""
        if self.index is None:
            return []
        
        vector = vector.reshape(1, -1)
        scores, indices = self.index.search(vector, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                doc = self.metadata[idx]
                results.append({
                    'id': idx,
                    'title': doc.get('title', 'Unknown'),
                    'content': doc.get('content', '')[:500],
                    'similarity': float(1 / (1 + score))
                })
        
        return results
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Get a specific document by its index ID"""
        if self.metadata and 0 <= doc_id < len(self.metadata):
            return self.metadata[doc_id]
        return None
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector database"""
        stats = {
            'index_size': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'metadata_count': len(self.metadata) if self.metadata else 0,
        }
        
        if self.stats:
            stats.update(self.stats)
        
        return stats