#!/usr/bin/env python3
"""Quick script to test database connection"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages', 'common', 'src'))

from uepi_common.config import get_settings
from sqlalchemy import create_engine, text
import time

settings = get_settings()
db_url = settings.database.url

print(f"Testing database connection...")
print(f"Database URL: {db_url[:50]}...")  # Don't print full password

try:
    # Test with timeout
    print("\n1. Creating engine with 5 second connection timeout...")
    engine = create_engine(
        db_url,
        connect_args={
            "connect_timeout": 5,
        },
        pool_pre_ping=True,
    )
    
    print("2. Attempting to connect...")
    start_time = time.time()
    
    with engine.connect() as conn:
        elapsed = time.time() - start_time
        print(f"   ✅ Connection successful! (took {elapsed:.2f} seconds)")
        
        print("3. Testing simple query...")
        start_time = time.time()
        result = conn.execute(text("SELECT 1"))
        elapsed = time.time() - start_time
        print(f"   ✅ Query successful! (took {elapsed:.2f} seconds)")
        
        print("4. Testing database name...")
        result = conn.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        print(f"   ✅ Connected to database: {db_name}")
        
        print("5. Testing table count...")
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        table_count = result.scalar()
        print(f"   ✅ Found {table_count} tables in database")
        
except Exception as e:
    elapsed = time.time() - start_time if 'start_time' in locals() else 0
    print(f"\n   ❌ Connection FAILED after {elapsed:.2f} seconds")
    print(f"   Error: {type(e).__name__}: {e}")
    print("\nPossible issues:")
    print("  - PostgreSQL is not running")
    print("  - Wrong connection string (host, port, user, password, database)")
    print("  - Firewall blocking connection")
    print("  - Database doesn't exist")
    print("\nTo check if PostgreSQL is running:")
    print("  ps aux | grep postgres")
    print("\nTo check connection manually:")
    print(f"  psql {db_url}")
    sys.exit(1)

print("\n✅ All database tests passed!")
