"""
Check if the vector database is working correctly
"""

import pickle
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
from pathlib import Path


class DatabaseValidator:
    def __init__(self):
        # File locations for the FAISS index and metadata
        self.faiss_index_path = r"data\vector_databases\main_index\faiss_index.bin"
        self.faiss_metadata_path = r"data\vector_databases\main_index\faiss_metadata.pkl"
        self.results = {}

    def check_faiss(self):
        """Load and verify the FAISS index and metadata"""

        print("\n" + "=" * 60)
        print("Checking FAISS vector database")
        print("=" * 60)

        # Make sure files exist first
        if not Path(self.faiss_index_path).exists():
            print(f"Missing index file: {self.faiss_index_path}")
            return False

        if not Path(self.faiss_metadata_path).exists():
            print(f"Missing metadata file: {self.faiss_metadata_path}")
            return False

        try:
            # Load FAISS index
            print("\nLoading FAISS index...")
            index = faiss.read_index(self.faiss_index_path)

            print("Index loaded successfully")
            print(f"Vector count: {index.ntotal:,}")
            print(f"Dimensions: {index.d}")

            # Load metadata
            print("\nLoading metadata...")
            with open(self.faiss_metadata_path, "rb") as f:
                data = pickle.load(f)

            # Support both newer and older formats
            if isinstance(data, dict):
                documents = data.get("documents", [])
                metadatas = data.get("metadatas", [])
                print("Metadata format: dictionary")
            else:
                metadatas = data
                documents = [f"Doc_{i}" for i in range(len(metadatas))]
                print("Metadata format: legacy list")

            print(f"Documents: {len(documents):,}")
            print(f"Metadata entries: {len(metadatas):,}")

            # Check consistency
            if index.ntotal == len(documents) == len(metadatas):
                print(f"\nCounts match: {index.ntotal:,}")
            else:
                print("\nCount mismatch detected")
                print(f"Vectors: {index.ntotal}")
                print(f"Documents: {len(documents)}")
                print(f"Metadata: {len(metadatas)}")

            # Show a sample entry
            if metadatas:
                print("\nSample document:")
                first = metadatas[0]

                print(f"Title: {first.get('title', 'No title')[:70]}")
                print(f"Source type: {first.get('source_type', 'Unknown')}")

                if first.get("url"):
                    print(f"URL: {first.get('url')[:60]}")

            # Breakdown by source type
            if metadatas and isinstance(metadatas[0], dict):
                df = pd.DataFrame(metadatas)

                if "source_type" in df.columns:
                    print("\nDocuments by source type:")
                    counts = df["source_type"].value_counts()

                    for source, count in counts.items():
                        print(f" - {source}: {count:,}")

            self.results["total_vectors"] = index.ntotal
            self.results["metadata_count"] = len(metadatas)

            return True, index, documents, metadatas

        except Exception as e:
            print(f"\nFailed to load vector database: {e}")
            return False, None, None, None

    def test_search(self, index, documents, metadatas):
        """Run a quick search test"""

        print("\n" + "=" * 60)
        print("Testing search functionality")
        print("=" * 60)

        try:
            print("\nLoading embedding model...")
            model = SentenceTransformer("all-MiniLM-L6-v2")
            print("Model loaded")

            test_queries = [
                "Zheng He voyages",
                "Ming dynasty ships",
                "Chinese exploration",
                "1421 hypothesis"
            ]

            print(f"\nRunning {len(test_queries)} test searches")

            for query in test_queries:
                print(f"\nQuery: {query}")

                vector = model.encode([query])[0].reshape(1, -1).astype("float32")
                distances, indices = index.search(vector, 3)

                found_any = False

                for i, idx in enumerate(indices[0]):
                    if idx < len(metadatas):
                        found_any = True
                        meta = metadatas[idx]
                        score = 1 / (1 + distances[0][i])

                        title = meta.get("title", "No title")[:60]
                        print(f"  {i + 1}. [{score:.3f}] {title}")

                if not found_any:
                    print("  No results returned")

            print("\nSearch test completed successfully")
            return True

        except Exception as e:
            print(f"\nSearch test failed: {e}")
            return False

    def run(self):
        """Run full validation process"""

        print("\n" + "=" * 60)
        print("VECTOR DATABASE CHECK")
        print("=" * 60)

        ok, index, docs, metas = self.check_faiss()

        if ok:
            self.test_search(index, docs, metas)

            print("\n" + "=" * 60)
            print("Summary")
            print("=" * 60)

            print(f"Total vectors: {self.results.get('total_vectors', 0):,}")
            print(f"Metadata entries: {self.results.get('metadata_count', 0):,}")

            print("\nVector database is ready to use")
        else:
            print("\nVector database is not valid or missing")
            print("You likely need to rebuild the index")

if __name__ == "__main__":
    validator = DatabaseValidator()
    validator.run()