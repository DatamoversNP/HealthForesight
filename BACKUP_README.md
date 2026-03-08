# HealthForesight Project Backup & Restore Guide

This guide explains how to create a complete backup of your HealthForesight project and restore it later in Cursor or any IDE.

## Creating a Backup

### Quick Backup

Simply run the backup script from the project root:

```bash
chmod +x backup.sh
./backup.sh
```

This will:
- Create a timestamped backup in `~/HealthForesight-Backups/`
- Exclude regenerable dependencies (node_modules, __pycache__, venv, etc.)
- Create a compressed `.tar.gz` archive
- Include all source code, configuration, and data files

### Manual Backup

If you prefer to create a backup manually:

1. **Exclude dependencies** that can be regenerated:
   - `node_modules/`
   - `__pycache__/`, `*.pyc`
   - `venv/`, `.venv/`, `env/`
   - `dist/`, `build/`
   - `.git/` (unless you want git history)
   - `*.log`
   - `.DS_Store`

2. **Include essential files**:
   - All source code (`apps/`, `packages/`, `scripts/`)
   - Configuration files (`pyproject.toml`, `package.json`, `.env`)
   - Data files (`data/`)
   - Documentation (`*.md`)
   - Infrastructure (`infra/`)

3. **Create archive**:
   ```bash
   tar -czf healthforesight_backup_$(date +%Y%m%d).tar.gz \
     --exclude='node_modules' \
     --exclude='__pycache__' \
     --exclude='venv' \
     --exclude='.venv' \
     --exclude='dist' \
     --exclude='build' \
     --exclude='.git' \
     --exclude='*.log' \
     .
   ```

## Restoring a Backup

### Automatic Restore

1. **Extract the backup**:
   ```bash
   cd ~/HealthForesight-Backups
   tar -xzf healthforesight_backup_YYYYMMDD_HHMMSS.tar.gz
   cd healthforesight-uepi_backup_YYYYMMDD_HHMMSS
   ```

2. **Run the restore script**:
   ```bash
   chmod +x restore.sh
   ./restore.sh
   ```

The restore script will:
- Check for required tools (Python, Node.js, Poetry)
- Install Python dependencies using Poetry
- Install Node.js dependencies using npm
- Set up environment files
- Verify the installation

### Manual Restore

1. **Extract the backup** to your desired location:
   ```bash
   tar -xzf healthforesight_backup_YYYYMMDD_HHMMSS.tar.gz -C /path/to/workspace
   ```

2. **Install Python dependencies**:
   ```bash
   cd /path/to/workspace
   poetry install
   ```
   
   If Poetry is not installed:
   ```bash
   pip install poetry
   poetry install
   ```

3. **Install Node.js dependencies**:
   ```bash
   cd apps/web
   npm install
   ```

4. **Set up environment variables**:
   ```bash
   cd /path/to/workspace
   cp .env.example .env  # If .env.example exists
   # Edit .env with your configuration
   ```

5. **Verify installation**:
   ```bash
   # Check Python dependencies
   poetry show
   
   # Check Node dependencies
   cd apps/web
   npm list
   ```

## Opening in Cursor

1. **Open Cursor IDE**

2. **Open the project**:
   - File > Open Folder (or `Cmd+O` on Mac, `Ctrl+O` on Windows/Linux)
   - Navigate to your restored project directory
   - Click "Open"

3. **Cursor should automatically**:
   - Detect the project type (Python + TypeScript/React)
   - Load workspace settings
   - Index files for search

4. **Start development servers**:
   ```bash
   # Terminal 1: API Server
   ./start-api-server.sh
   
   # Terminal 2: Web Server
   cd apps/web
   npm run dev
   
   # Or start both at once
   ./start-both-servers.sh
   ```

## Backup Location

Backups are stored in: `~/HealthForesight-Backups/`

Each backup includes:
- Timestamped directory with all files
- Compressed `.tar.gz` archive
- `BACKUP_INFO.txt` with backup details
- `RESTORE_INSTRUCTIONS.txt` with restoration guide

## What's Included in Backups

### ✅ Included:
- All source code (Python, TypeScript, React)
- Configuration files (pyproject.toml, package.json, vite.config.ts)
- Data files (data/)
- Documentation (*.md files)
- Infrastructure code (infra/)
- Scripts (start-*.sh, backup.sh, restore.sh)
- Environment files (.env.example)

### ❌ Excluded (can be regenerated):
- `node_modules/` → `npm install`
- `__pycache__/`, `*.pyc` → Automatically regenerated
- `venv/`, `.venv/` → `poetry install`
- `dist/`, `build/` → Build outputs
- `.git/` → Use `git clone` if needed
- `*.log` → Log files
- IDE-specific files (`.vscode`, `.idea`, `.cursor`)

## Troubleshooting

### Poetry Installation Issues
```bash
# Install Poetry
pip install poetry

# Or use the official installer
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"
```

### Node.js Installation Issues
```bash
# Check Node.js version (requires 18+)
node --version

# If not installed, download from: https://nodejs.org/
# Or use nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

### Environment Variable Issues
- Ensure `.env` file exists in project root
- Check `STORAGE_PATH` points to correct data directory
- Verify API and web server ports are available (8000, 3050, 3051)

### Missing Dependencies
```bash
# Reinstall Python dependencies
poetry install --no-cache

# Reinstall Node dependencies
cd apps/web
rm -rf node_modules package-lock.json
npm install
```

## Backup Best Practices

1. **Regular Backups**: Create backups before major changes
2. **Multiple Locations**: Store backups in multiple locations (local, cloud, external drive)
3. **Version Control**: Use Git for code history (backups are for complete snapshots)
4. **Test Restores**: Periodically test restoring from backups to ensure they work

## Backup Automation

You can schedule automatic backups using cron:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/project/backup.sh
```

## Questions or Issues?

If you encounter issues with backup or restore:
1. Check `BACKUP_INFO.txt` in the backup directory
2. Review `RESTORE_INSTRUCTIONS.txt`
3. Check server logs: `api-server.log`, `web-server.log`
4. Verify all prerequisites are installed (Python, Node.js, Poetry)
