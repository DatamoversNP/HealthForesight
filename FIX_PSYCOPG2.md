# Fix: ModuleNotFoundError: No module named 'psycopg2'

## Problem
The `psycopg2-binary` package is not installed in your Python environment.

## Solution

### Option 1: Install psycopg2-binary (Quick Fix)

```bash
pip3 install psycopg2-binary
```

Then run the database creation again:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"

cd apps/api
python3 -c "
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '../../packages/common/src')
from uepi_api.database import init_db
init_db()
print('✅ Database tables created!')
"
```

### Option 2: Install All Dependencies

Install all required packages from requirements.txt:

```bash
cd apps/api
pip3 install -r requirements.txt
```

### Option 3: Use Alembic (Recommended)

Alembic will handle dependencies better:

```bash
# 1. Install psycopg2-binary
pip3 install psycopg2-binary

# 2. Install Alembic if not already installed
pip3 install alembic

# 3. Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"

# 4. Run migrations
cd apps/api
alembic upgrade head
```

### Option 4: Use the Setup Script

```bash
# 1. Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"

# 2. Run setup script
cd apps/api/scripts
./setup_database.sh
```

## Verify Installation

Check if psycopg2 is installed:

```bash
python3 -c "import psycopg2; print('✅ psycopg2 installed:', psycopg2.__version__)"
```

## Troubleshooting

### If pip3 install fails with permission errors:

```bash
# Use --user flag
pip3 install --user psycopg2-binary

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install psycopg2-binary
```

### If you get "No module named 'psycopg2'" after installation:

- Make sure you're using the same Python interpreter
- Check Python path: `python3 -c "import sys; print(sys.path)"`
- Try: `python3 -m pip install psycopg2-binary`

### Alternative: Use psycopg (newer version)

If `psycopg2-binary` doesn't work, try the newer `psycopg`:

```bash
pip3 install psycopg[binary]
```

Then update the database URL to use `postgresql+psycopg://` instead of `postgresql://`.

