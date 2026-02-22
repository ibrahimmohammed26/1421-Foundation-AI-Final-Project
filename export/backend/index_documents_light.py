#!/usr/bin/env python3
"""
Comprehensive document indexing script for 1421 Foundation
This script will index ALL documents from the data folder into FAISS and SQLite
"""

import os
import sys
import pickle
import sqlite3
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
from datetime import datetime

# Add parent directory to path so we can import from backend
sys.path.append(str(Path(__file__).parent.parent))

import faiss
import numpy as np
import tqdm
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    JSONLoader,
    Docx2txtLoader,
    UnstructuredEPubLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader
)

# Configure paths
BASE_DIR = Path(__file__).parent.parent.parent  # Goes up to project root
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = DATA_DIR / "vector_databases" / "main_index"
DB_PATH = DATA_DIR / "knowledge_base.db"

# Supported file extensions and their loaders
LOADER_MAPPING = {
    ".txt": TextLoader,
    ".pdf": PyPDFLoader,
    ".csv": CSVLoader,
    ".md": UnstructuredMarkdownLoader,
    ".html": UnstructuredHTMLLoader,
    ".htm": UnstructuredHTMLLoader,
    ".json": JSONLoader,
    ".docx": Docx2txtLoader,
    ".doc": Docx2txtLoader,
    ".epub": UnstructuredEPubLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".ppt": UnstructuredPowerPointLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
}

def get_file_loader(file_path: Path):
    """Get the appropriate loader for a file based on its extension."""
    ext = file_path.suffix.lower()
    loader_class = LOADER_MAPPING.get(ext)
    if loader_class:
        try:
            if ext == ".json":
                return loader_class(str(file_path), jq_schema=".", text_content=False)
            return loader_class(str(file_path))
        except Exception as e:
            print(f"  ⚠️ Error creating loader for {file_path}: {e}")
            return None
    return None

def extract_metadata_from_path(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from file path and name."""
    metadata = {
        "source_file": str(file_path),
        "file_name": file_path.name,
        "file_size": file_path.stat().st_size,
        "file_type": file_path.suffix.lower(),
        "folder": str(file_path.parent.relative_to(DATA_DIR)) if file_path.parent != DATA_DIR else "root",
        "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
    }
    
    # Try to extract year from filename or path
    import re
    year_match = re.search(r'(1[4-9]\d{2}|20\d{2})', file_path.name)
    if year_match:
        metadata["year"] = int(year_match.group(1))
    
    # Try to extract author from filename
    author_match = re.search(r'by[_\s-]([A-Za-z]+)', file_path.name.lower())
    if author_match:
        metadata["author"] = author_match.group(1).title()
    
    return metadata

def chunk_document(doc: LCDocument, file_path: Path) -> List[Dict[str, Any]]:
    """Split document into chunks and prepare for indexing."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    
    chunks = text_splitter.split_documents([doc])
    chunked_docs = []
    
    for i, chunk in enumerate(chunks):
        # Create a unique ID for this chunk
        chunk_id = hashlib.md5(f"{file_path}_{i}_{chunk.page_content[:100]}".encode()).hexdigest()[:16]
        
        # Combine metadata
        metadata = {
            **doc.metadata,
            "chunk_id": chunk_id,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "content_preview": chunk.page_content[:500] + ("..." if len(chunk.page_content) > 500 else ""),
            "source_file": str(file_path),
        }
        
        chunked_docs.append({
            "id": chunk_id,
            "content": chunk.page_content,
            "metadata": metadata
        })
    
    return chunked_docs

def scan_and_load_documents():
    """Scan data directory and load all documents."""
    all_chunks = []
    stats = {
        "files_processed": 0,
        "files_failed": 0,
        "total_chunks": 0,
        "by_type": {},
        "by_folder": {}
    }
    
    print(f"\n🔍 Scanning data directory: {DATA_DIR}")
    
    # Recursively find all files
    all_files = list(DATA_DIR.rglob("*"))
    files_to_process = [f for f in all_files if f.is_file() and f.suffix.lower() in LOADER_MAPPING]
    
    print(f"Found {len(files_to_process)} supported files to process\n")
    
    # Process each file with progress bar
    for file_path in tqdm(files_to_process, desc="Processing files"):
        ext = file_path.suffix.lower()
        stats["by_type"][ext] = stats["by_type"].get(ext, 0) + 1
        
        folder = str(file_path.parent.relative_to(DATA_DIR)) if file_path.parent != DATA_DIR else "root"
        stats["by_folder"][folder] = stats["by_folder"].get(folder, 0) + 1
        
        try:
            loader = get_file_loader(file_path)
            if not loader:
                stats["files_failed"] += 1
                continue
            
            # Load the document
            docs = loader.load()
            
            # Add file metadata
            file_metadata = extract_metadata_from_path(file_path)
            for doc in docs:
                doc.metadata.update(file_metadata)
            
            # Chunk the document
            chunks = chunk_document(docs[0] if len(docs) == 1 else LCDocument(
                page_content="\n".join([d.page_content for d in docs]),
                metadata=file_metadata
            ), file_path)
            
            all_chunks.extend(chunks)
            stats["files_processed"] += 1
            stats["total_chunks"] += len(chunks)
            
        except Exception as e:
            print(f"\n  ❌ Error processing {file_path}: {e}")
            stats["files_failed"] += 1
    
    return all_chunks, stats

def create_embeddings_and_index(chunks: List[Dict[str, Any]]):
    """Create embeddings and build FAISS index."""
    if not chunks:
        print("❌ No chunks to index")
        return None, None, None
    
    print(f"\n🧠 Creating embeddings for {len(chunks)} chunks...")
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    # Extract texts
    texts = [chunk["content"] for chunk in chunks]
    
    # Create embeddings in batches
    batch_size = 100
    all_embeddings = []
    
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
        batch = texts[i:i+batch_size]
        batch_embeddings = embeddings.embed_documents(batch)
        all_embeddings.extend(batch_embeddings)
    
    # Convert to numpy array
    embeddings_array = np.array(all_embeddings).astype('float32')
    
    # Create FAISS index
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)
    
    print(f"✅ Created FAISS index with {index.ntotal} vectors of dimension {dimension}")
    
    return index, embeddings_array, chunks

def save_to_database(index, chunks):
    """Save index and chunks to files and SQLite."""
    # Create directories if they don't exist
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save FAISS index
    index_path = VECTOR_DB_DIR / "faiss_index.bin"
    faiss.write_index(index, str(index_path))
    print(f"✅ Saved FAISS index to {index_path}")
    
    # Prepare metadata for FAISS
    metadata = {}
    for i, chunk in enumerate(chunks):
        metadata[str(i)] = {
            "id": chunk["id"],
            "content_preview": chunk["metadata"]["content_preview"],
            "source_file": chunk["metadata"]["source_file"],
            "chunk_index": chunk["metadata"]["chunk_index"],
            "title": Path(chunk["metadata"]["source_file"]).stem,
            "type": chunk["metadata"].get("file_type", "unknown"),
            "year": chunk["metadata"].get("year", 0),
            "author": chunk["metadata"].get("author", "Unknown"),
        }
    
    # Save metadata
    metadata_path = VECTOR_DB_DIR / "faiss_metadata.pkl"
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"✅ Saved metadata to {metadata_path}")
    
    # Save to SQLite
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT,
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
            embedding_id INTEGER,
            folder TEXT,
            last_modified TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Clear existing data
    cursor.execute("DELETE FROM documents")
    
    # Insert chunks
    for i, chunk in enumerate(chunks):
        metadata = chunk["metadata"]
        cursor.execute("""
            INSERT INTO documents 
            (id, title, author, year, type, description, content_preview, 
             source_file, page_number, file_size, language, embedding_id, folder, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk["id"],
            Path(metadata["source_file"]).stem,
            metadata.get("author", "Unknown"),
            metadata.get("year", 0),
            metadata.get("file_type", "unknown"),
            f"Document from {metadata['source_file']}",
            metadata["content_preview"],
            metadata["source_file"],
            metadata.get("chunk_index", 0),
            metadata.get("file_size", 0),
            "en",
            i,
            metadata.get("folder", "root"),
            metadata.get("last_modified", "")
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ Saved {len(chunks)} chunks to SQLite database")

def print_stats(stats):
    """Print indexing statistics."""
    print("\n" + "="*50)
    print("📊 INDEXING STATISTICS")
    print("="*50)
    print(f"Files processed: {stats['files_processed']}")
    print(f"Files failed: {stats['files_failed']}")
    print(f"Total chunks created: {stats['total_chunks']}")
    
    print("\n📁 By file type:")
    for ext, count in stats["by_type"].items():
        print(f"  {ext}: {count}")
    
    print("\n📂 By folder:")
    for folder, count in sorted(stats["by_folder"].items()):
        if count > 0:
            print(f"  {folder}: {count}")

def main():
    parser = argparse.ArgumentParser(description="Index all documents for 1421 Foundation")
    parser.add_argument("--reset", action="store_true", help="Reset existing index")
    parser.add_argument("--no-embed", action="store_true", help="Skip embedding creation (metadata only)")
    args = parser.parse_args()
    
    print("\n" + "="*50)
    print("🚀 1421 FOUNDATION - DOCUMENT INDEXER")
    print("="*50)
    
    # Check OpenAI API key
    if not os.getenv("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"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-key'")
        return
    
    # Reset if requested
    if args.reset and VECTOR_DB_DIR.exists():
        import shutil
        print("🔄 Resetting existing index...")
        shutil.rmtree(VECTOR_DB_DIR)
        if DB_PATH.exists():
            DB_PATH.unlink()
    
    # Scan and load documents
    chunks, stats = scan_and_load_documents()
    
    if not chunks:
        print("❌ No documents found to index")
        return
    
    print_stats(stats)
    
    # Create embeddings and index
    index, embeddings_array, chunks = create_embeddings_and_index(chunks)
    
    if index:
        # Save to database
        save_to_database(index, chunks)
        
        print("\n" + "="*50)
        print("✅ INDEXING COMPLETE!")
        print("="*50)
        print(f"Total vectors in FAISS: {index.ntotal}")
        print(f"Total chunks in SQLite: {len(chunks)}")
        print(f"Vector dimension: {index.d}")
        print("\nYou can now:")
        print("  • Search documents semantically")
        print("  • Use RAG in chat")
        print("  • Browse documents in the Documents page")
    else:
        print("❌ Indexing failed")

if __name__ == "__main__":
    main()