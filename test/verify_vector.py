"""
Complete Vector Database Validation Script
Tests both SQLite database and Vector database to ensure everything works
"""

import sqlite3
import pickle
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np


class DatabaseValidator:
    def __init__(self, sqlite_path="knowledge_base_clean.db",
                 faiss_index="faiss_index.bin",
                 faiss_metadata="faiss_metadata.pkl"):
        self.sqlite_path = sqlite_path
        self.faiss_index = faiss_index
        self.faiss_metadata = faiss_metadata
        self.validation_results = {}

    def validate_sqlite(self):
        """Validate SQLite database"""
        print("=" * 70)
        print("1️⃣  VALIDATING SQLITE DATABASE")
        print("=" * 70)

        try:
            conn = sqlite3.connect(self.sqlite_path)

            # Check tables
            print("\n📋 Checking tables...")
            tables = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table'",
                conn
            )
            print(f"✅ Found {len(tables)} tables:")
            for table in tables['name']:
                print(f"   - {table}")

            # Check all_documents table
            print("\n📊 Analyzing all_documents table...")

            # Row count
            count_query = "SELECT COUNT(*) as count FROM all_documents"
            total_rows = pd.read_sql_query(count_query, conn)['count'][0]
            print(f"✅ Total rows: {total_rows:,}")
            self.validation_results['sqlite_total_rows'] = total_rows

            # Check columns
            columns = pd.read_sql_query("PRAGMA table_info(all_documents)", conn)
            print(f"✅ Columns ({len(columns)}):")
            for _, col in columns.iterrows():
                print(f"   - {col['name']:20} ({col['type']})")

            # Check content quality
            print("\n🔍 Checking content quality...")
            quality_query = """
                            SELECT COUNT(*)                                               as total, \
                                   SUM(CASE WHEN content IS NOT NULL THEN 1 ELSE 0 END)   as has_content, \
                                   SUM(CASE WHEN LENGTH(content) > 100 THEN 1 ELSE 0 END) as substantial_content, \
                                   AVG(LENGTH(content))                                   as avg_content_length, \
                                   MIN(LENGTH(content))                                   as min_length, \
                                   MAX(LENGTH(content))                                   as max_length
                            FROM all_documents \
                            """
            quality = pd.read_sql_query(quality_query, conn).iloc[0]

            print(f"   Total documents: {quality['total']:,}")
            print(
                f"   Has content: {quality['has_content']:,} ({quality['has_content'] / quality['total'] * 100:.1f}%)")
            print(
                f"   Substantial (>100 chars): {quality['substantial_content']:,} ({quality['substantial_content'] / quality['total'] * 100:.1f}%)")
            print(f"   Avg length: {quality['avg_content_length']:.0f} characters")
            print(f"   Min length: {quality['min_length']:.0f} characters")
            print(f"   Max length: {quality['max_length']:.0f} characters")

            self.validation_results['sqlite_has_content'] = quality['has_content']
            self.validation_results['sqlite_substantial'] = quality['substantial_content']

            # Check source types
            print("\n📁 Source type distribution:")
            source_query = """
                           SELECT source_type, COUNT(*) as count
                           FROM all_documents
                           GROUP BY source_type
                           ORDER BY count DESC \
                           """
            sources = pd.read_sql_query(source_query, conn)
            for _, row in sources.iterrows():
                print(f"   {row['source_type']:30} {row['count']:>6,}")

            self.validation_results['sqlite_sources'] = sources.to_dict('records')

            # Sample data
            print("\n📄 Sample document (first row):")
            sample = pd.read_sql_query(
                "SELECT title, author, source_type, LENGTH(content) as content_len FROM all_documents LIMIT 1",
                conn
            ).iloc[0]
            print(f"   Title: {sample['title']}")
            print(f"   Author: {sample['author']}")
            print(f"   Source: {sample['source_type']}")
            print(f"   Content length: {sample['content_len']} chars")

            conn.close()

            print("\n✅ SQLite database validation PASSED")
            return True

        except Exception as e:
            print(f"\n❌ SQLite validation FAILED: {e}")
            return False

    def validate_faiss(self):
        """Validate FAISS vector database"""
        print("\n" + "=" * 70)
        print("2️⃣  VALIDATING FAISS VECTOR DATABASE")
        print("=" * 70)

        try:
            # Load FAISS index
            print("\n📥 Loading FAISS index...")
            index = faiss.read_index(self.faiss_index)
            print(f"✅ Index loaded successfully")
            print(f"   Total vectors: {index.ntotal:,}")
            print(f"   Dimensions: {index.d}")

            self.validation_results['faiss_vectors'] = index.ntotal
            self.validation_results['faiss_dimensions'] = index.d

            # Load metadata
            print("\n📥 Loading metadata...")
            with open(self.faiss_metadata, 'rb') as f:
                data = pickle.load(f)
                documents = data['documents']
                metadatas = data['metadatas']

            print(f"✅ Metadata loaded successfully")
            print(f"   Documents: {len(documents):,}")
            print(f"   Metadata entries: {len(metadatas):,}")

            self.validation_results['faiss_documents'] = len(documents)
            self.validation_results['faiss_metadata'] = len(metadatas)

            # Validate consistency
            print("\n🔍 Checking consistency...")
            if index.ntotal == len(documents) == len(metadatas):
                print(f"✅ All counts match: {index.ntotal:,}")
            else:
                print(f"⚠️  WARNING: Counts don't match!")
                print(f"   Vectors: {index.ntotal:,}")
                print(f"   Documents: {len(documents):,}")
                print(f"   Metadata: {len(metadatas):,}")

            # Check metadata structure
            print("\n📋 Metadata structure (first entry):")
            if metadatas:
                first_meta = metadatas[0]
                for key, value in first_meta.items():
                    print(f"   {key:20} : {str(value)[:50]}")

            # Check source distribution
            print("\n📁 Source type distribution in vectors:")
            df_meta = pd.DataFrame(metadatas)
            if 'source_type' in df_meta.columns:
                source_counts = df_meta['source_type'].value_counts()
                for source, count in source_counts.items():
                    percentage = (count / len(df_meta)) * 100
                    print(f"   {source:30} {count:>6,} ({percentage:>5.1f}%)")

            print("\n✅ FAISS vector database validation PASSED")
            return True, index, documents, metadatas

        except Exception as e:
            print(f"\n❌ FAISS validation FAILED: {e}")
            return False, None, None, None

    def test_search_functionality(self, index, documents, metadatas):
        """Test actual search functionality"""
        print("\n" + "=" * 70)
        print("3️⃣  TESTING SEARCH FUNCTIONALITY")
        print("=" * 70)

        try:
            # Load embedding model
            print("\n🔤 Loading embedding model...")
            model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Model loaded")

            # Test queries
            test_queries = [
                "Zheng He Chinese explorer voyages",
                "Ming dynasty maritime exploration",
                "evidence Chinese discovery America",
                "Gavin Menzies 1421 hypothesis",
                "criticism of 1421 theory"
            ]

            print(f"\n🔍 Running {len(test_queries)} test searches...")

            for i, query in enumerate(test_queries, 1):
                print(f"\n{'─' * 70}")
                print(f"Test {i}: '{query}'")
                print(f"{'─' * 70}")

                # Generate embedding
                query_embedding = model.encode(query).reshape(1, -1).astype('float32')

                # Search
                distances, indices = index.search(query_embedding, 3)

                # Display results
                for rank, (idx, distance) in enumerate(zip(indices[0], distances[0]), 1):
                    if idx >= len(documents):
                        continue

                    similarity = 1 / (1 + distance)

                    print(f"\n   Result {rank}: (Similarity: {similarity:.3f})")

                    if idx < len(metadatas):
                        meta = metadatas[idx]
                        print(f"      Source: {meta.get('source_type', 'Unknown')}")
                        print(f"      Title: {meta.get('title', 'No title')[:60]}")

                    # Show snippet
                    doc_preview = documents[idx][:150].replace('\n', ' ')
                    print(f"      Preview: {doc_preview}...")

            print("\n✅ Search functionality test PASSED")
            return True

        except Exception as e:
            print(f"\n❌ Search functionality test FAILED: {e}")
            return False

    def cross_validate(self):
        """Cross-validate SQLite vs FAISS"""
        print("\n" + "=" * 70)
        print("4️⃣  CROSS-VALIDATION (SQLite vs FAISS)")
        print("=" * 70)

        try:
            sqlite_docs = self.validation_results.get('sqlite_substantial', 0)
            faiss_docs = self.validation_results.get('faiss_documents', 0)

            print(f"\n📊 Document counts:")
            print(f"   SQLite (substantial content): {sqlite_docs:,}")
            print(f"   FAISS (vectorized): {faiss_docs:,}")

            if sqlite_docs > 0:
                coverage = (faiss_docs / sqlite_docs) * 100
                print(f"   Coverage: {coverage:.1f}%")

                if coverage >= 95:
                    print("✅ Excellent coverage!")
                elif coverage >= 80:
                    print("⚠️  Good coverage, but some documents may be missing")
                else:
                    print("❌ Low coverage - many documents not vectorized")

                self.validation_results['coverage'] = coverage

            return True

        except Exception as e:
            print(f"❌ Cross-validation failed: {e}")
            return False

    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY REPORT")
        print("=" * 70)

        # Overall status
        print("\n✅ VALIDATION COMPLETE\n")

        # Key metrics
        print("Key Metrics:")
        print(f"  SQLite Documents: {self.validation_results.get('sqlite_total_rows', 0):,}")
        print(f"  Vectorized Documents: {self.validation_results.get('faiss_documents', 0):,}")
        print(f"  Vector Dimensions: {self.validation_results.get('faiss_dimensions', 0)}")
        print(f"  Coverage: {self.validation_results.get('coverage', 0):.1f}%")

        # Source breakdown
        print("\nSource Distribution:")
        sources = self.validation_results.get('sqlite_sources', [])
        for source in sources[:5]:  # Top 5
            print(f"  {source['source_type']:30} {source['count']:>6,}")

        # Recommendations
        print("\n💡 Recommendations:")
        coverage = self.validation_results.get('coverage', 0)

        if coverage >= 95:
            print("  ✅ Database is ready for production use")
            print("  ✅ Proceed to build the LLM interface")
        elif coverage >= 80:
            print("  ⚠️  Consider re-running vectorization for missing documents")
            print("  ✅ Can proceed with caution")
        else:
            print("  ❌ Significant documents missing from vector database")
            print("  ❌ Re-run vectorization before proceeding")

        # Export to file
        print("\n💾 Exporting report...")
        report_path = "validation_report.txt"

        with open(report_path, 'w') as f:
            f.write("VECTOR DATABASE VALIDATION REPORT\n")
            f.write("=" * 70 + "\n\n")

            for key, value in self.validation_results.items():
                f.write(f"{key}: {value}\n")

        print(f"✅ Report saved to: {report_path}")

        return self.validation_results


def main():
    """Run complete validation"""

    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "VECTOR DATABASE VALIDATION SUITE" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝\n")

    validator = DatabaseValidator()

    # Step 1: Validate SQLite
    sqlite_ok = validator.validate_sqlite()

    if not sqlite_ok:
        print("\n❌ Cannot proceed - SQLite validation failed")
        return

    # Step 2: Validate FAISS
    faiss_ok, index, documents, metadatas = validator.validate_faiss()

    if not faiss_ok:
        print("\n❌ Cannot proceed - FAISS validation failed")
        return

    # Step 3: Test search
    search_ok = validator.test_search_functionality(index, documents, metadatas)

    # Step 4: Cross-validate
    validator.cross_validate()

    # Step 5: Generate report
    results = validator.generate_report()

    # Final decision
    print("\n" + "=" * 70)
    print("🎯 NEXT STEPS")
    print("=" * 70)

    coverage = results.get('coverage', 0)

    if coverage >= 80:
        print("\n✅ DATABASE IS READY!")
        print("\nYou can now proceed to:")
        print("  1. Build the LLM interface with dual output (text + graphs)")
        print("  2. Connect to OpenAI/Claude API")
        print("  3. Create Streamlit app")
        print("\nRun: python build_llm_interface.py")
    else:
        print("\n⚠️  FIX REQUIRED")
        print("\nBefore proceeding:")
        print("  1. Re-run: python 2_create_vector_db.py")
        print("  2. Check for errors in vectorization")
        print("  3. Validate again")


if __name__ == "__main__":
    main()