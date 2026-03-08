# Fix DNS Conflict Error

## Problem
You're getting: **"Record name www conflicts with another record"**

This means there's already a DNS record for "www" that conflicts with the CNAME you're trying to add.

## Solution: Remove Conflicting Record First

### Step 1: Find the Conflicting Record

1. **Scroll up or down** in your DNS management page
2. **Look for any existing record** with:
   - Name: `www`
   - Could be an A record, CNAME, or other type

### Step 2: Delete the Conflicting Record

1. **Find the conflicting "www" record**
2. **Click the trash can icon** (🗑️) to delete it
3. **Confirm deletion**

### Step 3: Add the Correct CNAME Record

Now you can add the CNAME record:
- **Type:** `CNAME`
- **Name:** `www`
- **Value:** `aab8b42551af9ef7.vercel-dns-017.com.` (with trailing dot)
- **TTL:** `1/2 Hour` (or default)

## Common Conflicting Records

The conflict is usually caused by:

1. **Old A record for www:**
   - Type: A
   - Name: www
   - Value: Some IP address
   - **Action:** Delete this A record

2. **Old CNAME for www:**
   - Type: CNAME
   - Name: www
   - Value: Something else
   - **Action:** Delete this old CNAME

3. **Redirect/Forward record:**
   - Some providers use redirects
   - **Action:** Remove any www redirects

## Step-by-Step Fix

1. ✅ **A Record is correct** (216.198.79.1) - Keep this!
2. ❌ **Find and delete** any existing "www" record
3. ✅ **Add new CNAME** record for www with Vercel value
4. 💾 **Save all changes**
5. ⏱️ **Wait 5-60 minutes** for DNS propagation
6. 🔄 **Refresh in Vercel** to verify

## After Fixing

Once you've:
- Deleted the conflicting www record
- Added the correct CNAME for www
- Saved changes

Wait 5-60 minutes, then:
1. Go back to Vercel domain settings
2. Click "Refresh" next to both domains
3. The "Invalid Configuration" should disappear
4. Status should show "Valid Configuration" ✅

## Quick Checklist

- [ ] A record for @ is set: `216.198.79.1` ✅ (You have this)
- [ ] Old www record is deleted ❌ (Do this first)
- [ ] New CNAME for www is added: `aab8b42551af9ef7.vercel-dns-017.com.` (Do this after deleting old one)
- [ ] All changes saved
- [ ] Wait 5-60 minutes
- [ ] Refresh in Vercel

Your A record looks perfect! Just need to fix the www CNAME conflict.
