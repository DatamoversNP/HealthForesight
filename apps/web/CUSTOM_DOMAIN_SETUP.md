# Custom Domain Setup - healthforesight.ai

## Current Status
- ✅ Site is live on Vercel
- ✅ Domain added to Vercel project
- ⚠️ DNS records need to be configured at your domain provider

## Step-by-Step DNS Configuration

### Step 1: Go to Your Domain Provider

Log in to where you purchased `healthforesight.ai` (e.g., GoDaddy, Namecheap, Google Domains, etc.)

### Step 2: Add DNS Records

You need to add **2 DNS records**:

#### Record 1: Root Domain (healthforesight.ai)
- **Type:** `A`
- **Name/Host:** `@` (or leave blank, or use `healthforesight.ai`)
- **Value/Points to:** `216.198.79.1`
- **TTL:** 3600 (or default)

#### Record 2: WWW Subdomain (www.healthforesight.ai)
- **Type:** `CNAME`
- **Name/Host:** `www`
- **Value/Points to:** `aab8b42551af9ef7.vercel-dns-017.com.`
- **TTL:** 3600 (or default)

**Important:** Make sure the CNAME value ends with a dot (`.`) - `aab8b42551af9ef7.vercel-dns-017.com.`

### Step 3: Save and Wait

1. **Save** the DNS records at your domain provider
2. **Wait 5-60 minutes** for DNS propagation
3. **Refresh** the Vercel domain page (click the "Refresh" button)

## Common Domain Providers Instructions

### GoDaddy
1. Go to "My Products" → Click "DNS" next to your domain
2. Click "Add" to add new record
3. For A record: Type `A`, Name `@`, Value `216.198.79.1`, TTL `600`
4. For CNAME: Type `CNAME`, Name `www`, Value `aab8b42551af9ef7.vercel-dns-017.com.`, TTL `600`
5. Save both records

### Namecheap
1. Go to Domain List → Click "Manage" next to your domain
2. Go to "Advanced DNS" tab
3. Click "Add New Record"
4. Add A record: Type `A Record`, Host `@`, Value `216.198.79.1`, TTL `Automatic`
5. Add CNAME: Type `CNAME Record`, Host `www`, Value `aab8b42551af9ef7.vercel-dns-017.com.`, TTL `Automatic`
6. Save all changes

### Google Domains
1. Go to "DNS" section
2. Click "Custom records"
3. Add A record: Name `@`, Type `A`, Data `216.198.79.1`
4. Add CNAME: Name `www`, Type `CNAME`, Data `aab8b42551af9ef7.vercel-dns-017.com.`
5. Save

### Cloudflare
1. Go to your domain → DNS → Records
2. Add A record: Type `A`, Name `@`, IPv4 address `216.198.79.1`, Proxy status `DNS only` (gray cloud)
3. Add CNAME: Type `CNAME`, Name `www`, Target `aab8b42551af9ef7.vercel-dns-017.com.`, Proxy status `DNS only`
4. Save

## Verify DNS Records

After adding the records, verify they're correct:

### Using Command Line:
```bash
# Check A record
dig healthforesight.ai A

# Check CNAME record
dig www.healthforesight.ai CNAME
```

### Using Online Tools:
- https://dnschecker.org
- https://mxtoolbox.com/DNSLookup.aspx

Enter your domain and check if the records match what Vercel expects.

## After DNS Propagates

1. **Go back to Vercel** domain settings
2. **Click "Refresh"** button next to each domain
3. The "Invalid Configuration" warning should disappear
4. Status should change to "Valid Configuration" ✅
5. SSL certificate will be automatically issued (takes 1-5 minutes)

## Troubleshooting

### Still showing "Invalid Configuration" after 1 hour?

1. **Double-check the records:**
   - A record value must be exactly: `216.198.79.1`
   - CNAME value must be exactly: `aab8b42551af9ef7.vercel-dns-017.com.` (with trailing dot)

2. **Remove conflicting records:**
   - Delete any old A records pointing to other IPs
   - Delete any old CNAME records for www pointing elsewhere

3. **Check for typos:**
   - Make sure there are no extra spaces
   - CNAME must end with a dot (`.`)

4. **Wait longer:**
   - DNS can take up to 48 hours (usually 5-60 minutes)
   - Different regions propagate at different speeds

### Domain redirects to www but www doesn't work?

This is expected! Vercel is configured to redirect `healthforesight.ai` → `www.healthforesight.ai`. Once both DNS records are set up correctly, both will work.

### Want to use root domain instead of www?

1. In Vercel domain settings, click "Edit" on `healthforesight.ai`
2. Remove the redirect to www
3. Make sure the A record is set correctly
4. Both domains will work independently

## Expected Timeline

- **DNS Propagation:** 5-60 minutes (can be up to 48 hours)
- **SSL Certificate:** 1-5 minutes after DNS is valid
- **Full Setup:** Usually complete within 1 hour

## Once Complete

Your site will be accessible at:
- ✅ https://healthforesight.ai (redirects to www)
- ✅ https://www.healthforesight.ai
- ✅ https://healthforesight-marketing.vercel.app (still works)

All with automatic SSL certificates! 🎉
