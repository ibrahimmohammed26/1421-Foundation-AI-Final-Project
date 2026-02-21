import os
import pickle
import sqlite3
from pathlib import Path
from typing import List, Dict
import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain import RecursiveCharacterTextSplitter
from langchain_community import (
    TextLoader, PDFLoader, CSVLoader, 
    UnstructuredMarkdownLoader, UnstructuredHTMLLoader
)

def index_all_documents():
    """Index all documents from the data folder."""
    
    # Initialize
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    # Paths
    data_path = Path("data")
    vector_db_path = Path("data/vector_databases/main_index")
    vector_db_path.mkdir(parents=True, exist_ok=True)
    
    # Collect all documents
    all_docs = []
    all_metadata = []
    
    # Walk through all files in data directory
    for file_path in data_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.pdf', '.csv', '.md', '.html', '.json']:
            try:
                print(f"Processing: {file_path}")
                
                # Load document based on extension
                if file_path.suffix.lower() == '.txt':
                    loader = TextLoader(str(file_path))
                elif file_path.suffix.lower() == '.pdf':
                    loader = PDFLoader(str(file_path))
                elif file_path.suffix.lower() == '.csv':
                    loader = CSVLoader(str(file_path))
                elif file_path.suffix.lower() == '.md':
                    loader = UnstructuredMarkdownLoader(str(file_path))
                elif file_path.suffix.lower() == '.html':
                    loader = UnstructuredHTMLLoader(str(file_path))
                else:
                    continue
                
                docs = loader.load()
                
                # Split into chunks
                chunks = text_splitter.split_documents(docs)
                
                for i, chunk in enumerate(chunks):
                    doc_id = f"{file_path.stem}_{i}"
                    all_docs.append({
                        'id': doc_id,
                        'content': chunk.page_content,
                        'metadata': {
                            'source': str(file_path),
                            'page': i,
                            'title': file_path.stem,
                            'type': file_path.suffix[1:],
                            'path': str(file_path)
                        }
                    })
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    if not all_docs:
        print("No documents found to index")
        return
    
    # Create embeddings
    print(f"Creating embeddings for {len(all_docs)} chunks...")
    texts = [doc['content'] for doc in all_docs]
    embeddings_list = embeddings.embed_documents(texts)
    
    # Create FAISS index
    dimension = len(embeddings_list[0])
    index = faiss.IndexFlatL2(dimension)
    vectors = np.array(embeddings_list).astype('float32')
    index.add(vectors)
    
    # Save FAISS index
    faiss.write_index(index, str(vector_db_path / "faiss_index.bin"))
    
    # Save metadata
    metadata = {}
    for i, doc in enumerate(all_docs):
        metadata[str(i)] = {
            'id': doc['id'],
            'title': doc['metadata']['title'],
            'source': doc['metadata']['source'],
            'type': doc['metadata']['type'],
            'page': doc['metadata']['page'],
            'content_preview': doc['content'][:500] + "..."
        }
    
    with open(vector_db_path / "faiss_metadata.pkl", 'wb') as f:
        pickle.dump(metadata, f)
    
    # Save to SQLite
    conn = sqlite3.connect("data/knowledge_base.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT DEFAULT 'Unknown',
            year INTEGER DEFAULT 0,
            type TEXT,
            description TEXT,
            tags TEXT,
            content_preview TEXT,
            source_file TEXT,
            page_number INTEGER,
            file_size INTEGER,
            language TEXT DEFAULT 'en',
            embedding_id INTEGER
        )
    """)
    
    for i, doc in enumerate(all_docs):
        cursor.execute("""
            INSERT OR REPLACE INTO documents 
            (id, title, type, description, content_preview, source_file, page_number, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc['id'],
            doc['metadata']['title'],
            doc['metadata']['type'],
            f"Document from {doc['metadata']['source']}",
            doc['content'][:500],
            doc['metadata']['source'],
            doc['metadata']['page'],
            i
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Indexed {len(all_docs)} document chunks")
    print(f"✓ FAISS index saved to {vector_db_path / 'faiss_index.bin'}")
    print(f"✓ Metadata saved to {vector_db_path / 'faiss_metadata.pkl'}")
    print(f"✓ SQLite database updated")

if __name__ == "__main__":
    index_all_documents()