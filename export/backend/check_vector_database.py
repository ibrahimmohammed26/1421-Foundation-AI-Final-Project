from pathlib import Path
import pickle
import json

print("="*60)
print("🔍 CHECKING VECTOR DATABASE FILES")
print("="*60)

# Correct paths - go up one level from backend to project root
project_root = Path(__file__).parent.parent.parent  # Goes up to 1421-Foundation-AI-Final-Project
data_dir = project_root / "data"

index_path = data_dir / "vector_databases" / "main_index" / "faiss_index.bin"
metadata_path = data_dir / "vector_databases" / "main_index" / "faiss_metadata.pkl"
stats_path = data_dir / "database_stats.json"

print(f"\n📁 Project root: {project_root}")
print(f"📁 Data directory: {data_dir}")

print(f"\n📁 File locations:")
print(f"FAISS index: {index_path}")
print(f"Metadata: {metadata_path}")
print(f"Stats: {stats_path}")

print(f"\n📁 File existence:")
print(f"FAISS index exists: {index_path.exists()}")
print(f"Metadata exists: {metadata_path.exists()}")
print(f"Stats file exists: {stats_path.exists()}")

if stats_path.exists():
    with open(stats_path, 'r') as f:
        stats = json.load(f)
        print(f"\n📊 Document count from stats: {stats.get('document_count', 0)}")

if metadata_path.exists():
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
        print(f"\n📄 Metadata type: {type(metadata)}")
        
        if isinstance(metadata, dict):
            print(f"Dictionary keys: {list(metadata.keys())}")
            for key in metadata.keys():
                print(f"  - {key}: {type(metadata[key])}, length: {len(metadata[key]) if hasattr(metadata[key], '__len__') else 'N/A'}")
        elif isinstance(metadata, list):
            print(f"List length: {len(metadata)}")
            if len(metadata) > 0:
                print(f"First item type: {type(metadata[0])}")
        else:
            print(f"Metadata content: {metadata}")

print("\n" + "="*60)