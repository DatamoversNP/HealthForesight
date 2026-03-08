#!/usr/bin/env python3
"""Find existing PostgreSQL database and tables"""

import sys
import psycopg2
from psycopg2 import sql

def find_existing_database():
    """Find existing database with tables"""
    print("="*80)
    print("FINDING EXISTING POSTGRESQL DATABASE")
    print("="*80)
    print()
    
    # Try different connection methods
    print("Step 1: Trying to connect to PostgreSQL...")
    conn = None
    
    # Try different users and methods
    connection_attempts = [
        {"database": "postgres", "user": "postgres", "host": "localhost", "password": ""},
        {"database": "postgres", "user": "postgres", "host": "localhost", "password": "postgres"},
        {"database": "postgres", "user": "", "host": "localhost"},  # Peer auth
        {"database": "postgres", "user": "nilesh", "host": "localhost"},  # Your username
    ]
    
    for attempt in connection_attempts:
        try:
            if "password" in attempt and attempt["password"]:
                conn = psycopg2.connect(**attempt)
            else:
                # Try without password
                params = {k: v for k, v in attempt.items() if k != "password" or v}
                conn = psycopg2.connect(**params)
            print(f"✅ Connected as user: {attempt.get('user', 'default')}")
            break
        except Exception as e:
            continue
    
    if not conn:
        print("❌ Could not connect with any method")
        print("   Trying to connect with current user (peer authentication)...")
        try:
            conn = psycopg2.connect(database="postgres")
            print("✅ Connected using peer authentication!")
        except Exception as e:
            print(f"❌ Could not connect: {e}")
            print()
            print("Please provide:")
            print("  1. PostgreSQL user name (e.g., postgres, your username)")
            print("  2. Database name (if different from 'uepi')")
            print("  3. Password (if required)")
            return 1
    
    try:
        cur = conn.cursor()
        
        # List all databases
        print()
        print("Step 2: Listing all databases...")
        cur.execute("""
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database 
            WHERE datistemplate = false
            ORDER BY datname
        """)
        databases = cur.fetchall()
        
        print(f"Found {len(databases)} databases:")
        for db_name, size in databases:
            print(f"   - {db_name} ({size})")
        
        # Check each database for tables
        print()
        print("Step 3: Checking databases for tables...")
        found_db = None
        found_tables = []
        
        for db_name, _ in databases:
            if db_name in ['postgres', 'template0', 'template1']:
                continue
            
            try:
                # Connect to this database - use same connection method that worked
                conn.close()
                # Try the same connection method that worked initially
                for attempt in connection_attempts:
                    try:
                        if "password" in attempt and attempt["password"]:
                            conn = psycopg2.connect(database=db_name, **{k: v for k, v in attempt.items() if k != "database"})
                        else:
                            params = {k: v for k, v in attempt.items() if k != "password" or v}
                            params["database"] = db_name
                            conn = psycopg2.connect(**params)
                        break
                    except:
                        continue
                
                if not conn:
                    # Last resort: try peer auth
                    try:
                        conn = psycopg2.connect(database=db_name)
                    except:
                        continue
                
                cur = conn.cursor()
                
                # Count tables
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                table_count = cur.fetchone()[0]
                
                if table_count > 0:
                    print(f"   ✅ {db_name}: {table_count} tables")
                    
                    # List important tables
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                    tables = [row[0] for row in cur.fetchall()]
                    
                    # Check for our important tables
                    important_tables = ['policies', 'observations', 'analyses', 'pipelines', 'baselines']
                    found_important = [t for t in important_tables if t in tables]
                    
                    if found_important:
                        print(f"      Found important tables: {', '.join(found_important)}")
                        if not found_db or len(found_important) > len(found_tables):
                            found_db = db_name
                            found_tables = found_important
                    
                    # Show first 10 tables
                    print(f"      Tables: {', '.join(tables[:10])}")
                    if len(tables) > 10:
                        print(f"      ... and {len(tables) - 10} more")
                else:
                    print(f"   ⚠️  {db_name}: No tables")
                    
            except Exception as e:
                print(f"   ❌ {db_name}: Error - {e}")
                continue
        
        conn.close()
        
        # Summary
        print()
        print("="*80)
        print("SUMMARY")
        print("="*80)
        
        if found_db:
            print(f"\n✅ Found database with data: {found_db}")
            print(f"   Important tables found: {', '.join(found_tables)}")
            print()
            print("To use this database, update config:")
            print(f"   Database: {found_db}")
            print(f"   User: postgres (or check what user owns the tables)")
            print()
            print("Or update packages/common/src/uepi_common/config.py:")
            print(f'   url: "postgresql://postgres@localhost:5432/{found_db}"')
        else:
            print("\n⚠️  No database found with expected tables")
            print("   You may need to:")
            print("   1. Run migrations to create tables")
            print("   2. Import/seed data")
            print("   3. Check if data is in a different database")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return 1

if __name__ == "__main__":
    sys.exit(find_existing_database())
