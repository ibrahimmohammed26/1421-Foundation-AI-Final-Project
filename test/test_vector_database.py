"""
Check if our vector database is working properly
"""

import pickle
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
from pathlib import Path

class DatabaseValidator:
    def __init__(self):
        # Your actual file locations
        self.faiss_index_path = r"data\vector_databases\main_index\faiss_index.bin"
        self.faiss_metadata_path = r"data\vector_databases\main_index\faiss_metadata.pkl"
        self.results = {}
    
    def check_faiss(self):
        """Check the vector database"""
        print("\n" + "="*60)
        print("CHECKING FAISS VECTOR DATABASE")
        print("="*60)
        
        # Check if files exist
        if not Path(self.faiss_index_path).exists():
            print(f"❌ Can't find: {self.faiss_index_path}")
            return False
        
        if not Path(self.faiss_metadata_path).exists():
            print(f"❌ Can't find: {self.faiss_metadata_path}")
            return False
        
        try:
            # Load the index
            print("\n📥 Loading FAISS index...")
            index = faiss.read_index(self.faiss_index_path)
            print(f"   ✅ Index loaded")
            print(f"   Vectors: {index.ntotal:,}")
            print(f"   Dimensions: {index.d}")
            
            # Load the metadata
            print("\n📥 Loading metadata...")
            with open(self.faiss_metadata_path, 'rb') as f:
                data = pickle.load(f)
            
            # Handle both formats
            if isinstance(data, dict):
                documents = data.get('documents', [])
                metadatas = data.get('metadatas', [])
                print(f"   Format: Dictionary")
            else:
                metadatas = data
                documents = [f"Doc_{i}" for i in range(len(metadatas))]
                print(f"   Format: List (older version)")
            
            print(f"   Documents: {len(documents):,}")
            print(f"   Metadata entries: {len(metadatas):,}")
            
            # Check if counts match
            if index.ntotal == len(documents) == len(metadatas):
                print(f"\n✅ All good - counts match: {index.ntotal:,}")
            else:
                print(f"\n⚠️ Count mismatch:")
                print(f"   Vectors: {index.ntotal}")
                print(f"   Docs: {len(documents)}")
                print(f"   Meta: {len(metadatas)}")
            
            # Show what's inside
            if metadatas and len(metadatas) > 0:
                print("\n📄 Sample document:")
                first = metadatas[0]
                print(f"   Title: {first.get('title', 'No title')[:70]}")
                print(f"   Type: {first.get('source_type', 'Unknown')}")
                if first.get('url'):
                    print(f"   URL: {first.get('url', '')[:60]}")
            
            # Count by source type
            if metadatas and isinstance(metadatas[0], dict):
                df = pd.DataFrame(metadatas)
                if 'source_type' in df.columns:
                    print("\n📂 Documents by source:")
                    counts = df['source_type'].value_counts()
                    for src, cnt in counts.items():
                        print(f"   {src}: {cnt:,}")
            
            self.results['total_vectors'] = index.ntotal
            self.results['metadata_count'] = len(metadatas)
            
            return True, index, documents, metadatas
            
        except Exception as e:
            print(f"\n❌ Failed: {e}")
            return False, None, None, None
    
    def test_search(self, index, documents, metadatas):
        """Try searching"""
        print("\n" + "="*60)
        print("TESTING SEARCH")
        print("="*60)
        
        try:
            print("\n📥 Loading sentence transformer...")
            model = SentenceTransformer('all-MiniLM-L6-v2')
            print("   ✅ Model ready")
            
            # Test queries
            queries = [
                "Zheng He voyages",
                "Ming dynasty ships", 
                "Chinese exploration",
                "1421 hypothesis"
            ]
            
            print(f"\n🔍 Running {len(queries)} test searches...")
            
            for q in queries:
                print(f"\nQuery: '{q}'")
                
                # Convert query to vector
                vec = model.encode([q])[0].reshape(1, -1).astype('float32')
                
                # Search
                distances, indices = index.search(vec, 3)
                
                # Show results
                found = False
                for i, idx in enumerate(indices[0]):
                    if idx < len(metadatas):
                        found = True
                        meta = metadatas[idx]
                        score = 1 / (1 + distances[0][i])
                        title = meta.get('title', 'No title')[:60]
                        print(f"   {i+1}. [{score:.3f}] {title}")
                
                if not found:
                    print("   No results found")
            
            print("\n✅ Search is working")
            return True
            
        except Exception as e:
            print(f"\n❌ Search failed: {e}")
            return False
    
    def run(self):
        """Run all checks"""
        print("\n" + "╔" + "═"*58 + "╗")
        print("║" + " "*18 + "VECTOR DB CHECK" + " "*30 + "║")
        print("╚" + "═"*58 + "╝")
        
        # Check FAISS
        ok, index, docs, metas = self.check_faiss()
        
        if ok:
            # Test search
            self.test_search(index, docs, metas)
            
            # Summary
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            print(f"✅ Total documents indexed: {self.results.get('total_vectors', 0):,}")
            print(f"✅ Metadata entries: {self.results.get('metadata_count', 0):,}")
            print("\n💡 Your vector database is ready to use!")
        else:
            print("\n❌ Vector database needs to be rebuilt")
            print("   Run your rebuild script first")

if __name__ == "__main__":
    validator = DatabaseValidator()
    validator.run()