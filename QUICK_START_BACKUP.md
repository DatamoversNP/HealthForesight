# Quick Backup & Restore Guide

## Create Backup (2 minutes)

```bash
./backup.sh
```

This creates a timestamped backup in `~/HealthForesight-Backups/` with:
- All source code
- Configuration files
- Data files
- Compressed archive (.tar.gz)

**What's excluded**: node_modules, venv, __pycache__, build artifacts (can be regenerated)

## Restore in Cursor (5 minutes)

### Step 1: Extract Backup
```bash
cd ~/HealthForesight-Backups
tar -xzf healthforesight-uepi_backup_YYYYMMDD_HHMMSS.tar.gz
cd healthforesight-uepi_backup_YYYYMMDD_HHMMSS
```

### Step 2: Run Restore Script
```bash
chmod +x restore.sh
./restore.sh
```

This automatically:
- Installs Python dependencies (Poetry)
- Installs Node.js dependencies (npm)
- Sets up environment files

### Step 3: Open in Cursor
1. Open Cursor IDE
2. File > Open Folder
3. Select the restored project directory

### Step 4: Start Servers
```bash
# Start both servers
./start-both-servers.sh

# Or separately:
# Terminal 1:
./start-api-server.sh

# Terminal 2:
cd apps/web && npm run dev
```

## Backup Location

All backups stored in: `~/HealthForesight-Backups/`

Each backup includes:
- Full project snapshot
- `RESTORE_INSTRUCTIONS.txt`
- `BACKUP_INFO.txt`

## Need More Help?

See `BACKUP_README.md` for detailed instructions and troubleshooting.
