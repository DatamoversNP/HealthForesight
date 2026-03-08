# 🚀 Deploy HealthForesight Marketing Website to Vercel

## Quick Deploy (No Global Install Needed)

You can deploy using `npx` without installing Vercel globally:

```bash
# 1. Navigate to web directory
cd apps/web

# 2. Build the site (optional - Vercel will build it)
npm run build:marketing

# 3. Deploy using npx (no install needed!)
npx vercel --prod
```

**That's it!** The first time, it will:
- Ask you to login (opens browser)
- Ask for project configuration (just press Enter for defaults)
- Deploy your site

Your site will be live at: `https://[your-project-name].vercel.app`

---

## Step-by-Step Instructions

### Option 1: Using npx (Recommended - No Install)

```bash
# Navigate to the web directory
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"

# Login to Vercel (first time only)
npx vercel login

# Deploy to production
npx vercel --prod
```

### Option 2: Install Vercel CLI Globally

If you prefer to install globally (requires sudo/admin):

```bash
# Install globally (may require sudo)
sudo npm install -g vercel

# Navigate to web directory
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/apps/web"

# Login
vercel login

# Deploy
vercel --prod
```

---

## What Happens During Deployment

1. **First Time:**
   - You'll be asked to login (browser opens)
   - You'll be asked to create a new project
   - Project name: `healthforesight-marketing` (or your choice)
   - Configuration: Press Enter to use defaults (vercel.json)

2. **Deployment:**
   - Vercel reads `vercel.json`
   - Runs build command: `npm run build:marketing`
   - Outputs to: `dist-marketing`
   - Deploys to global CDN
   - Provides live URL

3. **Result:**
   - Your site is live!
   - Automatic SSL certificate
   - Global CDN
   - Automatic deployments on git push (if connected)

---

## Alternative: Deploy via GitHub (Easiest)

If you prefer not to use CLI:

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Go to [vercel.com](https://vercel.com)**
   - Sign up / Login
   - Click "Add New Project"

3. **Import your GitHub repository**
   - Select your repository
   - Click "Import"

4. **Configure:**
   - **Framework Preset:** Vite
   - **Root Directory:** `apps/web`
   - **Build Command:** `npm run build:marketing`
   - **Output Directory:** `dist-marketing`
   - **Install Command:** `npm install`

5. **Click "Deploy"**

6. **Done!** Your site is live and will auto-deploy on every push.

---

## Custom Domain Setup

After deployment:

1. Go to your Vercel project dashboard
2. Click "Settings" → "Domains"
3. Add your domain (e.g., `marketing.healthforesight.com`)
4. Follow DNS instructions:
   - Add CNAME record pointing to Vercel
   - Or add A records (IPs provided by Vercel)
5. SSL certificate is automatic (takes a few minutes)

---

## Troubleshooting

### Build Fails

If the build fails, check:

```bash
# Test build locally first
cd apps/web
npm install
npm run build:marketing
```

If local build works, the issue might be:
- Node.js version (Vercel uses Node 18+)
- Missing dependencies
- TypeScript errors (we've disabled TS checking for marketing build)

### Routes Return 404

Make sure `vercel.json` exists in `apps/web/` with rewrite rules (already configured).

### Assets Not Loading

- Check that assets are in `public/` folder
- Verify paths are relative (not absolute)
- Check browser console for 404 errors

---

## Environment Variables (if needed)

If you need environment variables:

1. Go to Vercel project dashboard
2. Settings → Environment Variables
3. Add variables for Production, Preview, Development

---

## Continuous Deployment

Once connected to GitHub:
- Every push to `main` branch = automatic production deployment
- Every pull request = preview deployment
- Zero configuration needed!

---

## Quick Reference

```bash
# Deploy (using npx - no install)
cd apps/web
npx vercel --prod

# Deploy (if installed globally)
cd apps/web
vercel --prod

# View deployments
npx vercel ls

# View logs
npx vercel logs
```

---

## 🎉 You're Ready!

Your marketing website is configured and ready to deploy. Choose your method:

- **Fastest:** `npx vercel --prod` (no install needed)
- **Easiest:** GitHub integration via Vercel dashboard
- **Most Control:** Install CLI globally

**Recommended:** Start with `npx vercel --prod` - it's the fastest way to go live!
