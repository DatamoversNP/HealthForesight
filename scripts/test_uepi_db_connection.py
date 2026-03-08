#!/usr/bin/env python3
"""Test connection to uepi_db database with different methods"""

import sys
import psycopg2

def test_connections():
    """Try different connection methods to uepi_db"""
    print("="*80)
    print("TESTING CONNECTION TO uepi_db")
    print("="*80)
    print()
    
    # Try different connection methods
    methods = [
        {"database": "uepi_db", "user": "postgres", "host": "localhost"},  # TCP, no password
        {"database": "uepi_db", "user": "postgres", "host": "/tmp"},  # Unix socket
        {"database": "uepi_db"},  # Default (peer auth)
        {"database": "uepi_db", "user": "postgres", "host": "localhost", "password": ""},
        {"database": "uepi_db", "user": "postgres", "host": "localhost", "password": "postgres"},
    ]
    
    for i, params in enumerate(methods, 1):
        print(f"Method {i}: {params}")
        try:
            conn = psycopg2.connect(**params)
            cur = conn.cursor()
            
            # Test query
            cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            table_count = cur.fetchone()[0]
            
            # Check for important tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('policies', 'observations', 'analyses', 'pipelines', 'baselines')
                ORDER BY table_name
            """)
            important_tables = [row[0] for row in cur.fetchall()]
            
            # Count records in important tables
            print(f"   ✅ Connected!")
            print(f"   Tables: {table_count}")
            print(f"   Important tables found: {', '.join(important_tables)}")
            
            if important_tables:
                print()
                print("   Record counts:")
                for table in important_tables:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cur.fetchone()[0]
                        print(f"      - {table}: {count} records")
                    except:
                        print(f"      - {table}: Error counting")
            
            conn.close()
            print()
            print("="*80)
            print(f"✅ SUCCESS! Use this connection method:")
            print(f"   {params}")
            print("="*80)
            return params
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            print()
    
    print("❌ None of the connection methods worked")
    return None

if __name__ == "__main__":
    result = test_connections()
    if result:
        print()
        print("Update config to use:")
        if "password" in result and result["password"]:
            print(f'   url: "postgresql://{result["user"]}:{result["password"]}@{result["host"]}:5432/{result["database"]}"')
        elif "host" in result:
            print(f'   url: "postgresql://{result["user"]}@{result["host"]}:5432/{result["database"]}"')
        else:
            print(f'   url: "postgresql:///{result["database"]}"')
    sys.exit(0 if result else 1)
