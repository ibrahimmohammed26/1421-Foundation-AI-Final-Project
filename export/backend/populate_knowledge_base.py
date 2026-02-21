import sqlite3
import json
from pathlib import Path
import pickle

def create_knowledge_base():
    """Create SQLite database and populate with document metadata."""
    
    db_path = Path("data/knowledge_base.db")
    metadata_path = Path("data/vector_databases/main_index/faiss_metadata.pkl")
    
    # Connect to SQLite
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            year INTEGER,
            type TEXT,
            description TEXT,
            tags TEXT,
            content_preview TEXT,
            source_file TEXT,
            page_number INTEGER,
            file_size INTEGER,
            language TEXT DEFAULT 'en',
            full_content TEXT,
            embedding_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index on common search fields
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON documents(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON documents(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_author ON documents(author)")
    
    # Load metadata from FAISS pickle if it exists
    if metadata_path.exists():
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        # Insert documents from metadata
        for doc_id, doc_info in metadata.items():
            cursor.execute("""
                INSERT OR REPLACE INTO documents 
                (id, title, author, year, type, description, tags, source_file, embedding_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                doc_info.get('title', 'Unknown Title'),
                doc_info.get('author', 'Unknown Author'),
                doc_info.get('year', 0),
                doc_info.get('type', 'document'),
                doc_info.get('description', ''),
                ','.join(doc_info.get('tags', [])),
                doc_info.get('source_file', ''),
                doc_info.get('embedding_id', 0)
            ))
    
    # Sample documents if none exist
    cursor.execute("SELECT COUNT(*) as count FROM documents")
    if cursor.fetchone()[0] == 0:
        sample_docs = [
            (
                "1", "1421: The Year China Discovered the World", 
                "Gavin Menzies", 2002, "book",
                "Controversial book proposing that Chinese fleets circumnavigated the globe before Columbus.",
                "1421 hypothesis,exploration,Ming dynasty", "unknown", 0
            ),
            (
                "2", "Zheng He: China's Great Explorer",
                "Zhang Wei", 2015, "book",
                "Biography of Admiral Zheng He and his seven voyages.",
                "Zheng He,biography,Ming dynasty", "unknown", 1
            ),
            (
                "3", "Ming Dynasty Naval Technology",
                "Li Hua", 2020, "article",
                "Analysis of shipbuilding techniques and navigation methods during the Ming era.",
                "naval technology,shipbuilding,navigation", "unknown", 2
            ),
            (
                "4", "Treasure Fleet: The Secret Voyages of Zheng He",
                "Louise Levathes", 1994, "book",
                "Historical account of China's great explorer and his treasure ships.",
                "treasure fleet,Zheng He,exploration", "unknown", 3
            ),
            (
                "5", "Chinese Maritime Expansion: 1405-1433",
                "Chen Ming", 2018, "thesis",
                "Academic study of China's naval expeditions during the early Ming dynasty.",
                "maritime expansion,Ming dynasty,academic", "unknown", 4
            )
        ]
        
        for doc in sample_docs:
            cursor.execute("""
                INSERT INTO documents 
                (id, title, author, year, type, description, tags, source_file, embedding_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, doc)
    
    conn.commit()
    conn.close()
    print("Knowledge base created successfully!")

if __name__ == "__main__":
    create_knowledge_base()