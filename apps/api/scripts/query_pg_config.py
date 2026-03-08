#!/usr/bin/env python3
"""Query PostgreSQL to find pg_hba.conf location"""

import subprocess
import sys
import os

# Add PostgreSQL to PATH
os.environ['PATH'] = f"/usr/local/opt/postgresql@15/bin:/opt/homebrew/opt/postgresql@15/bin:{os.environ.get('PATH', '')}"

print("🔍 Querying PostgreSQL for configuration files...")
print("")

try:
    # Try to get hba_file location
    result = subprocess.run(
        ['psql', '-U', 'postgres', '-d', 'postgres', '-t', '-c', 'SHOW hba_file;'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0:
        hba_file = result.stdout.strip()
        if hba_file and os.path.exists(hba_file):
            print(f"✅ Found pg_hba.conf: {hba_file}")
            print("")
            print("To enable trust authentication, add these lines at the TOP:")
            print("  host    all             all             127.0.0.1/32            trust")
            print("  host    all             all             ::1/128                 trust")
            print("")
            print("Then restart PostgreSQL:")
            print("  brew services restart postgresql@15")
            sys.exit(0)
        else:
            print(f"⚠️  PostgreSQL reports: {hba_file}")
            print("   But file doesn't exist at that location")
    
    # Try to get data_directory
    result = subprocess.run(
        ['psql', '-U', 'postgres', '-d', 'postgres', '-t', '-c', 'SHOW data_directory;'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0:
        data_dir = result.stdout.strip()
        if data_dir:
            hba_path = os.path.join(data_dir, 'pg_hba.conf')
            if os.path.exists(hba_path):
                print(f"✅ Found pg_hba.conf: {hba_path}")
                print("")
                print("To enable trust authentication, add these lines at the TOP:")
                print("  host    all             all             127.0.0.1/32            trust")
                print("  host    all             all             ::1/128                 trust")
                print("")
                print("Then restart PostgreSQL:")
                print("  brew services restart postgresql@15")
                sys.exit(0)
            else:
                print(f"📁 Data directory: {data_dir}")
                print(f"   Expected pg_hba.conf at: {hba_path}")
                print(f"   But file doesn't exist")
    
except subprocess.TimeoutExpired:
    print("❌ Connection to PostgreSQL timed out")
    print("   Make sure PostgreSQL is running: brew services start postgresql@15")
except FileNotFoundError:
    print("❌ psql command not found")
    print("   Add PostgreSQL to PATH:")
    print("   export PATH=\"/usr/local/opt/postgresql@15/bin:\$PATH\"")
except Exception as e:
    print(f"❌ Error: {e}")
    print("")
    print("Try these commands manually:")
    print("  export PATH=\"/usr/local/opt/postgresql@15/bin:\$PATH\"")
    print("  psql -U postgres -d postgres -c \"SHOW hba_file;\"")
    print("  psql -U postgres -d postgres -c \"SHOW data_directory;\"")
    sys.exit(1)

print("")
print("Common locations to check manually:")
print("  /usr/local/var/postgresql@15/pg_hba.conf")
print("  /opt/homebrew/var/postgresql@15/pg_hba.conf")
print("  ~/Library/Application Support/Postgres/var-15/pg_hba.conf")

