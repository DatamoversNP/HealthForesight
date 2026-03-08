# Fix DNS Configuration - Current Status

Looking at your DNS records, here's what I see:

## ✅ What's Correct:
- **Row 1:** A record, Name `@`, Data `216.198.79.1` ✅ **PERFECT!**

## ❌ What Needs to be Fixed:

### 1. Delete Row 2 (WebsiteBuilder Site)
- **Row 2:** A record, Name `@`, Data `WebsiteBuilder Site`
- This is a GoDaddy Website Builder record that conflicts with Vercel
- **Action:** Click the trash can icon (🗑️) to **DELETE** this record

### 2. Add CNAME for WWW
- You're **missing** the CNAME record for `www`
- **Action:** Click "Add" or "+" button to add a new record:
  - **Type:** `CNAME`
  - **Name:** `www`
  - **Data:** `aab8b42551af9ef7.vercel-dns-017.com.` (with trailing dot!)
  - **TTL:** `1 Hour` (or default)

## Step-by-Step Actions:

### Step 1: Delete WebsiteBuilder Record
1. Find **Row 2** (A record with "WebsiteBuilder Site")
2. Click the **trash can icon** (🗑️) on that row
3. Confirm deletion

### Step 2: Add WWW CNAME Record
1. Click **"Add"** or **"+"** button (usually at top of table)
2. Select **Type:** `CNAME`
3. Enter **Name:** `www`
4. Enter **Data:** `aab8b42551af9ef7.vercel-dns-017.com.` (with dot at end!)
5. Set **TTL:** `1 Hour` (or default)
6. **Save** the record

### Step 3: Verify Final Configuration
After changes, you should have:
- ✅ A record: `@` → `216.198.79.1` (Row 1 - keep this!)
- ✅ CNAME record: `www` → `aab8b42551af9ef7.vercel-dns-017.com.` (new record)
- ❌ No "WebsiteBuilder Site" record (deleted)

### Step 4: Save and Wait
1. **Save** all changes
2. **Wait 5-60 minutes** for DNS propagation
3. Go back to **Vercel**
4. Click **"Refresh"** button on both domains
5. Status should change to "Valid Configuration" ✅

## Why the Old Records Aren't Showing

The old A records (76.223.105.230, 13.248.243.5) that Vercel mentioned might:
- Already be deleted
- Be hidden or shown differently in GoDaddy's interface
- Be part of the "WebsiteBuilder Site" record

The "WebsiteBuilder Site" record is likely the main conflict. Once you delete it and add the www CNAME, everything should work!

## Final DNS Configuration Should Be:

**Root Domain (healthforesight.ai):**
- A record: `@` → `216.198.79.1` ✅ (You have this)

**WWW Subdomain (www.healthforesight.ai):**
- CNAME: `www` → `aab8b42551af9ef7.vercel-dns-017.com.` (Need to add this)

**System Records (Don't Touch):**
- NS records (nameservers) - Can't delete, that's fine
- SOA record - Leave it
- TXT records - Leave them
- Other CNAMEs (pay, _domainconnect) - Leave them

## Quick Action Items:

1. [ ] Delete Row 2: A record with "WebsiteBuilder Site"
2. [ ] Add CNAME: `www` → `aab8b42551af9ef7.vercel-dns-017.com.`
3. [ ] Save all changes
4. [ ] Wait 5-60 minutes
5. [ ] Refresh in Vercel

You're almost there! Just need to remove the WebsiteBuilder record and add the www CNAME.
