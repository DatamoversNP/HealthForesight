# API is Using Database, Not File Storage

## The Problem

The API is currently using the **database** to return policies, not the file-based storage we set up.

## Evidence

- ✅ Our file has **8 policies** with predicted impact
- ❌ API returns **11 different policies** from database
- ❌ Policy IDs don't match between file and API

## Why This Happens

The API tries database first, and only uses file storage if the database is unavailable. Since the database query is succeeding, it uses the database.

## Solution Options

### Option 1: Make Database Unavailable (Force File Storage)
Stop/disconnect the database so API falls back to file storage.

### Option 2: Import Policies to Database
Import the policies from the file into the database.

### Option 3: Set USE_FILE_STORAGE=True
Ensure the API configuration forces file storage mode.

## Current Status

The policies you see in the UI are from the database, which is why:
- They have different IDs
- They don't have predicted impact
- Clicking Psychology icon returns 404

## Next Steps

We need to either:
1. Make the API use file storage instead of database, OR
2. Import our 8 policies (with predicted impact) into the database

Which approach would you prefer?
