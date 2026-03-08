# Fix Vercel DNS Conflicts

Vercel detected old/conflicting DNS records. Here's exactly what to do:

## Step 1: Remove OLD Records (Do This First!)

Go to your domain provider's DNS management and **DELETE** these records:

### For Root Domain (healthforesight.ai):
- ❌ **DELETE:** A record, Name `@`, Value `76.223.105.230`
- ❌ **DELETE:** A record, Name `@`, Value `13.248.243.5`

### For WWW Subdomain (www.healthforesight.ai):
- ❌ **DELETE:** A record, Name `www`, Value `76.223.105.230`
- ❌ **DELETE:** A record, Name `www`, Value `13.248.243.5`

## Step 2: Add NEW Records (After Deleting Old Ones)

### For Root Domain (healthforesight.ai):
- ✅ **ADD:** A record
  - Type: `A`
  - Name: `@` (or blank)
  - Value: `216.198.79.1`
  - TTL: `1/2 Hour` (or default)

### For WWW Subdomain (www.healthforesight.ai):
- ✅ **ADD:** CNAME record
  - Type: `CNAME`
  - Name: `www`
  - Value: `aab8b42551af9ef7.vercel-dns-017.com.` (with trailing dot!)
  - TTL: `1/2 Hour` (or default)

## Complete Checklist

### Root Domain (healthforesight.ai):
- [ ] Delete A record: `@` → `76.223.105.230`
- [ ] Delete A record: `@` → `13.248.243.5`
- [ ] Add A record: `@` → `216.198.79.1`

### WWW Subdomain (www.healthforesight.ai):
- [ ] Delete A record: `www` → `76.223.105.230`
- [ ] Delete A record: `www` → `13.248.243.5`
- [ ] Add CNAME record: `www` → `aab8b42551af9ef7.vercel-dns-017.com.`

## Important Notes

1. **Delete FIRST, then add** - Don't add new records until old ones are deleted
2. **CNAME value must end with dot:** `aab8b42551af9ef7.vercel-dns-017.com.`
3. **www should be CNAME, not A record** - This is important!
4. **Save all changes** at your domain provider

## After Making Changes

1. **Save** all DNS changes at your domain provider
2. **Wait 5-60 minutes** for DNS propagation
3. **Go back to Vercel**
4. **Click "Refresh"** button next to each domain
5. **Status should change** from "Invalid Configuration" to "Valid Configuration" ✅

## Why This Happened

You had old A records pointing to different IP addresses. Vercel needs:
- Root domain: New A record pointing to `216.198.79.1`
- WWW: CNAME record (not A record!) pointing to Vercel's DNS

## Timeline

- **DNS Changes:** Immediate (after you save)
- **DNS Propagation:** 5-60 minutes (can take up to 48 hours)
- **Vercel Verification:** After DNS propagates, click Refresh
- **SSL Certificate:** 1-5 minutes after Vercel verifies

## Verification

After 5-60 minutes, check:
1. Go to Vercel domain settings
2. Click "Refresh" on both domains
3. Should see "Valid Configuration" ✅
4. SSL certificate will be issued automatically

Your site will then be live at:
- ✅ https://healthforesight.ai
- ✅ https://www.healthforesight.ai
