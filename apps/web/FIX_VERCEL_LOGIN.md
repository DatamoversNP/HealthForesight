# Fix Vercel Login Issue

You're getting a token error. Here's how to fix it:

## Solution: Login to Vercel

Run these commands in your **terminal** (not in Cursor):

```bash
# 1. Navigate to web directory
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"

# 2. Login to Vercel (this will open your browser)
npx vercel login
```

**What happens:**
1. It will open your browser
2. You'll be asked to login to Vercel (or create account)
3. Authorize the CLI
4. You'll be redirected back to terminal
5. Login is complete!

**Then deploy:**
```bash
npx vercel --prod
```

---

## Alternative: Use GitHub Deployment (No CLI Needed)

If you're having issues with CLI login, use the web interface:

### Step 1: Push to GitHub (if not already)

```bash
# From project root
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Deploy via Vercel Dashboard

1. **Go to [vercel.com](https://vercel.com)**
   - Sign up (free) or login
   - Use GitHub to sign up (easiest)

2. **Click "Add New Project"**

3. **Import your GitHub repository**
   - Select your repository
   - Click "Import"

4. **Configure Project Settings:**
   - **Framework Preset:** Vite (or "Other")
   - **Root Directory:** Click "Edit" → Enter: `apps/web`
   - **Build Command:** `npm run build:marketing`
   - **Output Directory:** `dist-marketing`
   - **Install Command:** `npm install`

5. **Click "Deploy"**

6. **Done!** Your site will be live in ~2 minutes

---

## Why GitHub Deployment is Easier

- ✅ No CLI installation needed
- ✅ No login issues
- ✅ Visual interface
- ✅ Automatic deployments on every push
- ✅ Preview deployments for pull requests
- ✅ Easy to manage domains

---

## Troubleshooting CLI Login

If `npx vercel login` doesn't work:

1. **Clear old tokens:**
   ```bash
   rm -rf ~/.vercel
   ```

2. **Try again:**
   ```bash
   npx vercel login
   ```

3. **If browser doesn't open:**
   - Copy the URL from terminal
   - Paste in browser manually
   - Complete login
   - Return to terminal

---

## Recommended: Use GitHub Deployment

For the easiest experience, I recommend using the Vercel dashboard with GitHub integration. It's:
- Faster to set up
- No CLI issues
- Automatic deployments
- Better for teams

Just push your code to GitHub and use the web interface!
