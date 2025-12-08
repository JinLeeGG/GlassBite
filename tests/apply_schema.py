"""
Apply schema.sql to database
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
import psycopg2

def apply_schema():
    """Read and execute schema.sql"""
    
    # Use DATABASE_URL from Config
    db_url = Config.SQLALCHEMY_DATABASE_URI
    
    print(f"🔧 Connecting to database: {db_url}")
    
    # Connect using full URL
    conn = psycopg2.connect(db_url)
    
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Read schema.sql
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    print("🔧 Applying schema.sql...")
    
    # Execute schema
    try:
        cursor.execute(schema_sql)
        print("✅ Schema applied successfully!")
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    apply_schema()
