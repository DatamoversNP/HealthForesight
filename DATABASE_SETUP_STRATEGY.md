# Database Setup Strategy: Local vs Azure

## Quick Answer

**You have two options:**

### Option 1: Start with Local (Recommended for Development)
1. ✅ Set up PostgreSQL locally first
2. ✅ Test database creation and migrations locally
3. ✅ Verify everything works
4. ✅ Then set up Azure PostgreSQL for production

**Pros:**
- Faster development cycle
- No Azure costs during development
- Can work offline
- Easier to debug

### Option 2: Use Azure for Both (If you prefer)
1. ✅ Set up Azure PostgreSQL Flexible Server
2. ✅ Use it for both development and production
3. ✅ Connect from local machine to Azure database

**Pros:**
- One database to manage
- Production-like environment from start
- No local PostgreSQL needed

**Cons:**
- Requires internet connection
- Azure costs during development
- Slightly slower (network latency)

## Recommended Approach: Start Local, Then Azure

### Phase 1: Local Development (Now)

**Set up local PostgreSQL:**
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15
createdb uepi_db

# Set DATABASE_URL for local
export DATABASE_URL="postgresql://$(whoami)@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"

# Create tables
cd apps/api
python3 scripts/create_db_simple.py
```

**Benefits:**
- Test database migration locally
- Verify all 55 tables are created correctly
- Test dual-mode storage (file vs database)
- No Azure costs during testing

### Phase 2: Azure Production (When Ready)

**Set up Azure PostgreSQL Flexible Server:**
1. Create Azure PostgreSQL Flexible Server (no licensing cost - open source)
2. Get connection string from Azure portal
3. Update DATABASE_URL for Azure deployment
4. Run migrations on Azure

**Azure PostgreSQL Setup:**
```bash
# Get connection string from Azure portal
# Format: postgresql://username:password@server-name.postgres.database.azure.com:5432/uepi_db

export DATABASE_URL="postgresql://username:password@your-server.postgres.database.azure.com:5432/uepi_db"
export USE_FILE_STORAGE="false"

# Run migrations on Azure
cd apps/api
alembic upgrade head
```

## Do You Need Both Right Now?

**Short answer: NO**

**Start with local PostgreSQL:**
- ✅ Set up local PostgreSQL now
- ✅ Test database creation locally
- ✅ Verify migrations work
- ✅ Test the application with database mode

**Set up Azure PostgreSQL later:**
- ⏳ When you're ready to deploy to production
- ⏳ Or when you want to test in a production-like environment

## Current Status

✅ **Database models created**: 55 tables defined  
✅ **Alembic migrations created**: Migration file ready  
✅ **Dual-mode storage**: 32/37 files support both file and database  
⚠️  **Local PostgreSQL**: Needs to be set up and tested  
⏳ **Azure PostgreSQL**: Can be set up later for production

## Next Steps

1. **Now**: Set up local PostgreSQL and test database creation
2. **Later**: Set up Azure PostgreSQL when deploying to production

## Azure PostgreSQL - No Licensing Cost

Azure Database for PostgreSQL - Flexible Server is **open source** and has **no licensing costs**. You only pay for:
- Compute (server size)
- Storage
- Network egress

**Free tier available**: Azure offers a free tier for development/testing (with limitations).

## Summary

- **Local PostgreSQL**: Set up now for development and testing
- **Azure PostgreSQL**: Set up later for production deployment
- **You don't need both right now** - start with local, add Azure when ready

