# verify_database.py
import sqlite3
import pandas as pd


def verify_database():
    """Verify your current SQLite database"""

    db_path = 'knowledge_base_clean.db'

    print("=" * 70)
    print("🔍 VERIFYING YOUR SQLITE DATABASE")
    print("=" * 70)

    try:
        conn = sqlite3.connect(db_path)

        # 1. List all tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]

        print(f"\n📊 Found {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  📋 {table}: {count:,} rows")

        # 2. Show table structures
        print("\n🔧 Table Structures:")
        print("-" * 50)
        for table in tables:
            print(f"\n{table.upper()}:")
            df_info = pd.read_sql_query(f"PRAGMA table_info({table})", conn)
            for _, row in df_info.iterrows():
                print(f"  {row['name']} ({row['type']})")

        # 3. Sample queries
        print("\n💡 Sample Data:")
        print("-" * 50)

        # Try to find main documents table
        possible_tables = ['documents', 'all_documents', 'facebook_posts', 'gavin_menzies_docs']
        for table_name in possible_tables:
            if table_name in tables:
                df_sample = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn)
                if not df_sample.empty:
                    print(f"\n{table_name} (first 3 rows):")
                    print(df_sample[['title', 'content', 'url']].head(3).to_string())
                    break

        conn.close()

        print("\n" + "=" * 70)
        print("✅ YOUR DATABASE IS READY!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    verify_database()