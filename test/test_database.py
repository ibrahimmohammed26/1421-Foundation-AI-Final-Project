# verify_database.py
import sqlite3
import pandas as pd

"""Check of what's inside the SQLite database, and that it is working properly"""

def test_database():

    db_path = 'data\\knowledge_base.db'

    print("=" * 70)
    print("Checking SQLite database")
    print("=" * 70)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [
            row[0]
            for row in cursor.fetchall()
            if not row[0].startswith('sqlite_')
        ]

        print(f"\nFound {len(tables)} tables in database")

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f" - {table}: {count:,} rows")

        # 2. table structures
        print("\nTable structures")
        print("-" * 50)

        for table in tables:
            print(f"\n{table}:")
            df_info = pd.read_sql_query(f"PRAGMA table_info({table})", conn)

            for _, row in df_info.iterrows():
                print(f"   {row['name']} ({row['type']})")

        # 3. sample data check
        print("\nSample data preview")
        print("-" * 50)

        possible_tables = [
            'documents',
            'all_documents',
            'facebook_posts',
            'gavin_menzies_docs'
        ]

        for table_name in possible_tables:
            if table_name in tables:
                df_sample = pd.read_sql_query(
                    f"SELECT * FROM {table_name} LIMIT 3",
                    conn
                )
                if not df_sample.empty:
                    print(f"\nTable: {table_name} (first 3 rows)")

                    cols_to_show = [c for c in ['title', 'content', 'url'] if c in df_sample.columns]

                    if cols_to_show:
                        print(df_sample[cols_to_show].head(3).to_string())
                    else:
                        print(df_sample.head(3).to_string())


                    break

        conn.close()
        print("\n" + "=" * 70)
        print("Database check complete. Everything looks ready.")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"Error while checking database: {e}")
        return False


if __name__ == "__main__":
    test_database()