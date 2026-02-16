#!/usr/bin/env python
"""
Script to inspect your FAISS vector database files
Run this to understand your data structure
"""

import sys
import os
import pickle
import json
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("FAISS not installed. Run: pip install faiss-cpu")

def inspect_faiss_data(data_path="data/vector_databases"):
    """Inspect FAISS index and metadata"""
    
    data_dir = Path(data_path)
    if not data_dir.exists():
        print(f"❌ Directory not found: {data_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"INSPECTING FAISS VECTOR DATABASE")
    print(f"{'='*60}")
    print(f"Path: {data_dir.absolute()}")
    
    # List all files
    print(f"\n📁 FILES FOUND:")
    for file in data_dir.glob("*"):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  - {file.name} ({size_mb:.2f} MB)")
    
    # Check FAISS index
    index_file = data_dir / "faiss_index.bin"
    if index_file.exists() and HAS_FAISS:
        print(f"\n🔍 FAISS INDEX:")
        index = faiss.read_index(str(index_file))
        print(f"  - Number of vectors: {index.ntotal}")
        print(f"  - Vector dimension: {index.d}")
        print(f"  - Index type: {type(index).__name__}")
        print(f"  - Is trained: {index.is_trained}")
    
    # Check metadata
    metadata_file = data_dir / "faiss_metadata.pkl"
    if metadata_file.exists():
        print(f"\n📄 METADATA:")
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"  - Type: {type(metadata).__name__}")
        print(f"  - Length: {len(metadata)}")
        
        # Show sample
        if len(metadata) > 0:
            print(f"\n  Sample document (index 0):")
            sample = metadata[0]
            for key, value in list(sample.items())[:5]:  # First 5 fields
                if isinstance(value, str):
                    value = value[:100] + "..." if len(value) > 100 else value
                print(f"    - {key}: {value}")
    
    # Check stats
    stats_file = data_dir / "database_stats.json"
    if stats_file.exists():
        print(f"\n📊 STATISTICS:")
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        for key, value in stats.items():
            print(f"  - {key}: {value}")
    
    # Check if there's a docstore
    docstore_file = data_dir / "docstore.pkl"
    if docstore_file.exists():
        print(f"\n📚 DOCSTORE:")
        with open(docstore_file, 'rb') as f:
            docstore = pickle.load(f)
        print(f"  - Type: {type(docstore).__name__}")
        print(f"  - Length: {len(docstore)}")

if __name__ == "__main__":
    # You can pass a different path as argument
    path = sys.argv[1] if len(sys.argv) > 1 else "data/vector_databases"
    inspect_faiss_data(path)