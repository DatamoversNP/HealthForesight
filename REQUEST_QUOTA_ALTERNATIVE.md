# How to Request Azure Quota Increase - Alternative Methods

## Issue: Can't Find "App Service Plans - Free"

The quota section in Azure Portal can have different names or may not show all quotas. Here are alternative methods:

## Method 1: Through Support Request (Easiest) ✅

This is the most reliable way to request quota:

### Step 1: Open Support Request

1. Go to: https://portal.azure.com
2. In the top search bar, type: **"Help + support"**
3. Click **"Help + support"** service
4. Click **"+ New support request"** button

### Step 2: Fill Out Support Request

**Problem type:**
- Select: **"Service and subscription limits (quotas)"**

**Subscription:**
- Select your subscription

**Quota type:**
- Select: **"Compute - App Service Plans"**
- OR: **"App Service Plans"** if available
- OR: **"Other"** and type "App Service Plans - Free"

**Additional details:**
- **Region**: Select your preferred region (e.g., East US, West US)
- **Quota type**: App Service Plans - Free
- **Current limit**: 0
- **Requested limit**: 1 (minimum)

**Description:**
```
I need quota to deploy an App Service Plan for my application.

Current limit: 0
Requested limit: 1 (minimum)
Tier: Free (F1)
Region: [your region]

Reason: Deploying HealthForesight platform (FastAPI + React app) for development/testing purposes.
```

**Contact method:**
- Email or Phone (your choice)
- Contact details (auto-filled from your account)

### Step 3: Submit

Click **"Create"** or **"Submit"**

**Approval time**: Usually 24-48 hours (often faster for Free tier)

---

## Method 2: Direct Link to Support Request

Click this link to go directly to support request:
https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade/newsupportrequest

Then follow Method 1 above.

---

## Method 3: Through Subscriptions → Usage + Quotas

If you can't find "App Service Plans - Free", try these:

### Alternative Names to Look For:

1. **"App Service Plans"** (without "Free")
2. **"App Service - Free"**
3. **"Compute - App Service Plans"**
4. **"Web Hosting Plans"**
5. **"App Service (Linux)"**

### Steps:

1. Go to: https://portal.azure.com
2. Search: **"Subscriptions"**
3. Click: **"Subscriptions"** service
4. Click: Your subscription name
5. Left menu: **"Usage + quotas"**
6. **Filter** box: Type "App Service" or "Web Hosting"
7. Look through the list for any App Service related quotas

If you find one (even if it doesn't say "Free"), click it and request increase.

---

## Method 4: Via Azure CLI (Alternative)

If you prefer command line:

```bash
# Get your subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Get your subscription name
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)

echo "Subscription: $SUBSCRIPTION_NAME"
echo "Subscription ID: $SUBSCRIPTION_ID"
echo ""
echo "To request quota:"
echo "1. Go to: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade/newsupportrequest"
echo "2. Select: Service and subscription limits (quotas)"
echo "3. Select: Compute - App Service Plans"
echo "4. Use Subscription ID: $SUBSCRIPTION_ID"
```

---

## Method 5: Check All Available Quotas

Sometimes the quota might be listed under a different category:

### Step 1: View All Quotas

1. Go to: https://portal.azure.com
2. Search: **"Subscriptions"**
3. Click: Your subscription
4. Click: **"Usage + quotas"**
5. **Remove all filters** - View everything

### Step 2: Search for Related Terms

In the search/filter box, try:
- "App"
- "Service"
- "Web"
- "Compute"
- "Free"

Look through all results for anything related to App Service.

---

## What to Request

Even if you can't find the exact quota, you can still request it through support:

### Request Details:

**Quota Type**: App Service Plans - Free (F1)

**Region**: 
- East US (preferred)
- Or West US, Central US, etc.

**Current Limit**: 0

**Requested Limit**: 1 (minimum)

**Reason**: 
```
Need quota for App Service Plan to deploy application.
Tier: Free (F1)
Purpose: Development/Testing
```

---

## After Submitting Request

### Check Status:

1. Go to: **Help + support**
2. Click: **"Support requests"**
3. Find your request
4. Check status (usually "Open" → "In progress" → "Resolved")

### Check Quota (after approval):

1. Go to: **Subscriptions** → Your subscription → **Usage + quotas**
2. Search for: "App Service"
3. Check if limit has increased

---

## Alternative: Upgrade Subscription

If quota requests keep getting denied, consider:

### Upgrade to Pay-As-You-Go:

1. Go to: https://portal.azure.com
2. Search: **"Subscriptions"**
3. Click: Your subscription
4. Click: **"Upgrade subscription"** (if available)
5. Choose: **"Pay-As-You-Go"**

**Note**: Pay-As-You-Go subscriptions typically have more quota available.

---

## Quick Summary

### Best Method (Most Reliable):

✅ **Method 1: Support Request** - This always works!

1. Go to: https://portal.azure.com
2. Search: **"Help + support"**
3. Click: **"+ New support request"**
4. Select: **"Service and subscription limits (quotas)"**
5. Select: **"Compute - App Service Plans"** or **"Other"**
6. Fill details and submit

### After Approval:

Once quota is approved, run:
```bash
./DEPLOY_TO_AZURE.sh
```

---

## Troubleshooting

### "Can't find quota type in dropdown"

- Select **"Other"** in the quota type dropdown
- Type: "App Service Plans - Free" in the description

### "Request denied"

- Make sure you're requesting for Free tier (F1)
- Provide clear business reason
- Try a different region

### "No response after days"

- Check support request status in "Help + support"
- Azure usually responds within 24-48 hours
- For Free tier, often faster (hours)

---

## Summary

✅ **Use Support Request method** - Most reliable way to request quota
✅ **Select "Service and subscription limits (quotas)"**
✅ **Choose "Compute - App Service Plans" or "Other"**
✅ **Request 1 for Free tier (F1)**
✅ **Wait 24-48 hours** (often faster)
✅ **Run deployment script again** after approval

**The support request method works even if you can't find the quota in the Usage + Quotas section!**
