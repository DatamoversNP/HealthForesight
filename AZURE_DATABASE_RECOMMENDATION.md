# Azure Database Recommendation - Zero Licensing Costs

## Recommended: Azure Database for PostgreSQL

### Why PostgreSQL?

1. **✅ Zero Licensing Costs** - PostgreSQL is open source (BSD license)
2. **✅ Already Compatible** - Your codebase already uses PostgreSQL:
   - Uses `JSONB` (PostgreSQL-specific)
   - Uses `psycopg2` driver
   - Database validation in `database.py` requires PostgreSQL
3. **✅ Full Feature Support** - JSONB, UUID, advanced indexing, etc.
4. **✅ Azure Managed Service** - No server management needed

### Azure Options (No Licensing Fees):

#### Option 1: Azure Database for PostgreSQL - Flexible Server ⭐ **RECOMMENDED**

**Why Flexible Server:**
- ✅ Lower cost than Single Server
- ✅ Better performance control
- ✅ Zone redundancy available
- ✅ Better for production workloads
- ✅ Supports both development and production tiers

**Pricing Tiers (Pay only for compute + storage, no licensing):**

1. **Burstable (B-series)** - Best for development/testing
   - `B1ms`: 1 vCore, 2GB RAM - **~$12/month**
   - `B2s`: 2 vCores, 4GB RAM - **~$24/month**
   - Good for: Development, testing, low-traffic apps

2. **General Purpose** - Best for production
   - `D2s_v3`: 2 vCores, 8GB RAM - **~$100/month**
   - `D4s_v3`: 4 vCores, 16GB RAM - **~$200/month**
   - Good for: Production workloads, moderate traffic

3. **Memory Optimized** - For high-performance
   - `E2s_v3`: 2 vCores, 16GB RAM - **~$200/month**
   - `E4s_v3`: 4 vCores, 32GB RAM - **~$400/month**
   - Good for: High-performance, large datasets

**Storage:**
- Minimum: 32GB - **~$4/month**
- Additional: **~$0.12/GB/month**
- IOPS included (3 IOPS per GB, up to 20,000 IOPS)

**Cost Optimization Tips:**
- Start with `B1ms` for development: **~$16/month total**
- Use `D2s_v3` for production: **~$104/month total** (with 32GB storage)
- Use **Reserved Capacity** (1-3 year commitment): **30-50% discount**
- Use **Azure Hybrid Benefit** (if you have SQL Server licenses): Not applicable (PostgreSQL is free)
- **Stop/Start** dev servers when not in use: Save compute costs

#### Option 2: Azure Database for PostgreSQL - Single Server (Legacy)

**Not Recommended:**
- ❌ More expensive than Flexible Server
- ❌ Less control over performance
- ❌ Being phased out by Microsoft
- ⚠️ Still no licensing fees, but higher compute costs

#### Option 3: Self-Managed PostgreSQL on Azure VM

**Not Recommended:**
- ❌ You manage the server (patches, backups, monitoring)
- ❌ More operational overhead
- ❌ Still pay for VM compute (similar cost)
- ✅ Full control, but not worth the effort for managed service

### Cost Comparison:

| Option | Monthly Cost (Dev) | Monthly Cost (Prod) | Licensing |
|--------|-------------------|---------------------|-----------|
| **PostgreSQL Flexible Server (B1ms)** | **~$16** | N/A | **$0** ✅ |
| **PostgreSQL Flexible Server (D2s_v3)** | N/A | **~$104** | **$0** ✅ |
| **PostgreSQL Single Server** | ~$25 | ~$150 | **$0** ✅ |
| **Azure SQL Database** | ~$5 (Basic) | ~$150+ | **Included** (but higher compute cost) |
| **Self-Managed VM** | ~$30+ | ~$100+ | **$0** ✅ |

### Recommended Setup:

#### Development/Testing:
```bash
# Azure CLI command to create dev database
az postgres flexible-server create \
  --resource-group healthforesight-rg \
  --name healthforesight-db-dev \
  --location eastus \
  --admin-user uepiadmin \
  --admin-password <strong-password> \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --public-access 0.0.0.0 \
  --firewall-rules start-ip-address=0.0.0.0 end-ip-address=255.255.255.255
```

**Cost:** ~$16/month (can stop when not in use)

#### Production:
```bash
# Azure CLI command to create production database
az postgres flexible-server create \
  --resource-group healthforesight-rg \
  --name healthforesight-db-prod \
  --location eastus \
  --admin-user uepiadmin \
  --admin-password <strong-password> \
  --sku-name Standard_D2s_v3 \
  --tier GeneralPurpose \
  --storage-size 128 \
  --version 15 \
  --high-availability Enabled \
  --backup-retention 7
```

**Cost:** ~$120/month (with 128GB storage, high availability)

### Connection String Format:

```bash
# For Azure App Service
DATABASE_URL=postgresql://uepiadmin:password@healthforesight-db-prod.postgres.database.azure.com:5432/uepi_db?sslmode=require
```

### Security Best Practices:

1. **Firewall Rules:**
   - Allow only Azure App Service IPs
   - Or use Private Endpoint (more secure, slightly more expensive)

2. **SSL/TLS:**
   - Always use `sslmode=require` in connection string
   - Azure enforces SSL by default

3. **Authentication:**
   - Use strong passwords
   - Consider Azure AD authentication (future enhancement)

### Migration Path:

1. **Create Flexible Server** (dev tier)
2. **Run Alembic migrations** to create all tables
3. **Run data migration scripts** to move data from files
4. **Test thoroughly** on dev database
5. **Create production database** when ready
6. **Switch `USE_FILE_STORAGE=false`** in production
7. **Monitor costs** and optimize as needed

### Cost Monitoring:

```bash
# Set up cost alerts
az consumption budget create \
  --budget-name postgresql-monthly \
  --amount 150 \
  --time-grain Monthly \
  --start-date 2025-01-01 \
  --end-date 2025-12-31 \
  --category Cost \
  --resource-group healthforesight-rg
```

### Summary:

✅ **Use: Azure Database for PostgreSQL - Flexible Server**
- Zero licensing costs (PostgreSQL is open source)
- Already compatible with your codebase
- Cost-effective: ~$16/month (dev) to ~$120/month (prod)
- Fully managed by Azure
- Production-ready with high availability options

❌ **Avoid:**
- Azure SQL Database (SQL Server licensing included, but higher costs)
- Self-managed VMs (operational overhead)
- Single Server (legacy, more expensive)

### Next Steps:

1. Create dev database: `az postgres flexible-server create ...`
2. Update `DATABASE_URL` in Azure App Service settings
3. Set `USE_FILE_STORAGE=false`
4. Run migrations
5. Test and migrate data

