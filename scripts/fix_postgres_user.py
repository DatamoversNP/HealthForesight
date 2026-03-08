#!/usr/bin/env python3
"""Fix PostgreSQL user and database for local development"""

import sys
import psycopg2
from psycopg2 import sql

def try_connect_as_postgres():
    """Try to connect as postgres user (default admin)"""
    try:
        # Try common default connections
        connections = [
            {"user": "postgres", "password": "", "host": "localhost"},
            {"user": "postgres", "password": "postgres", "host": "localhost"},
            {"user": "nilesh", "password": "", "host": "localhost"},  # Your username
            {"user": "", "password": "", "host": "localhost"},  # Peer authentication
        ]
        
        for conn_params in connections:
            try:
                conn = psycopg2.connect(
                    database="postgres",
                    **conn_params
                )
                return conn
            except:
                continue
        return None
    except Exception as e:
        print(f"Error trying connections: {e}")
        return None

def fix_database():
    """Create/fix uepi user and database"""
    print("="*80)
    print("FIXING POSTGRESQL USER AND DATABASE")
    print("="*80)
    print()
    
    # Try to connect as postgres
    print("Step 1: Trying to connect to PostgreSQL...")
    conn = try_connect_as_postgres()
    
    if not conn:
        print("❌ Could not connect to PostgreSQL")
        print()
        print("Options:")
        print("1. PostgreSQL might not be running")
        print("2. You might need to install PostgreSQL locally")
        print("3. You might need to start PostgreSQL service")
        print()
        print("To install PostgreSQL on macOS:")
        print("  brew install postgresql@15")
        print("  brew services start postgresql@15")
        print()
        print("Or use Docker:")
        print("  docker run -d --name uepi-postgres -e POSTGRES_USER=uepi -e POSTGRES_PASSWORD=uepi123 -e POSTGRES_DB=uepi -p 5432:5432 postgres:15-alpine")
        return 1
    
    print("✅ Connected to PostgreSQL!")
    print()
    
    try:
        cur = conn.cursor()
        conn.autocommit = True
        
        # Check if user exists
        print("Step 2: Checking if user 'uepi' exists...")
        cur.execute("""
            SELECT 1 FROM pg_roles WHERE rolname = 'uepi'
        """)
        user_exists = cur.fetchone() is not None
        
        if not user_exists:
            print("   User 'uepi' does not exist. Creating...")
            cur.execute("""
                CREATE USER uepi WITH PASSWORD 'uepi123';
            """)
            print("   ✅ User 'uepi' created")
        else:
            print("   ✅ User 'uepi' already exists")
            # Update password to be sure
            print("   Updating password...")
            cur.execute("""
                ALTER USER uepi WITH PASSWORD 'uepi123';
            """)
            print("   ✅ Password updated")
        
        # Check if database exists
        print()
        print("Step 3: Checking if database 'uepi' exists...")
        cur.execute("""
            SELECT 1 FROM pg_database WHERE datname = 'uepi'
        """)
        db_exists = cur.fetchone() is not None
        
        if not db_exists:
            print("   Database 'uepi' does not exist. Creating...")
            cur.execute("""
                CREATE DATABASE uepi OWNER uepi;
            """)
            print("   ✅ Database 'uepi' created")
        else:
            print("   ✅ Database 'uepi' already exists")
        
        # Grant privileges
        print()
        print("Step 4: Granting privileges...")
        cur.execute("""
            GRANT ALL PRIVILEGES ON DATABASE uepi TO uepi;
        """)
        print("   ✅ Privileges granted")
        
        # Connect to uepi database to grant schema privileges
        conn.close()
        conn = try_connect_as_postgres()
        if conn:
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("""
                SELECT 1 FROM pg_database WHERE datname = 'uepi'
            """)
            if cur.fetchone():
                # Connect to uepi database
                conn.close()
                try:
                    conn = psycopg2.connect(
                        database="uepi",
                        user="postgres",
                        host="localhost"
                    )
                    conn.autocommit = True
                    cur = conn.cursor()
                    cur.execute("""
                        GRANT ALL ON SCHEMA public TO uepi;
                        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO uepi;
                    """)
                    print("   ✅ Schema privileges granted")
                except:
                    pass
        
        conn.close()
        
        print()
        print("="*80)
        print("✅ DATABASE SETUP COMPLETE!")
        print("="*80)
        print()
        print("User: uepi")
        print("Password: uepi123")
        print("Database: uepi")
        print()
        print("You can now test the connection:")
        print("  python3 scripts/fix_database_connection.py")
        print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return 1

if __name__ == "__main__":
    sys.exit(fix_database())
