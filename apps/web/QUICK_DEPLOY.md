# Quick Deploy Guide - HealthForesight Marketing Website

## 🚀 Fastest Way: Vercel (Recommended)

### Option A: Deploy via CLI (2 minutes)

```bash
# 1. Install Vercel CLI (one time)
npm install -g vercel

# 2. Navigate to web directory
cd apps/web

# 3. Login to Vercel
vercel login

# 4. Deploy!
vercel --prod
```

**That's it!** Your site will be live in ~2 minutes at a URL like:
`https://healthforesight-marketing.vercel.app`

---

### Option B: Deploy via GitHub (Automatic)

1. **Push your code to GitHub** (if not already)
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Go to [vercel.com](https://vercel.com)** and sign up/login

3. **Click "Add New Project"**

4. **Import your GitHub repository**

5. **Configure:**
   - Framework Preset: **Vite**
   - Root Directory: `apps/web`
   - Build Command: `npm run build:marketing`
   - Output Directory: `dist-marketing`

6. **Click "Deploy"**

7. **Done!** Every push to main will auto-deploy.

---

## 🌐 Alternative: Netlify

```bash
# 1. Install Netlify CLI
npm install -g netlify-cli

# 2. Navigate to web directory
cd apps/web

# 3. Login
netlify login

# 4. Deploy
netlify deploy --prod
```

Or use the Netlify dashboard and connect your GitHub repo (same process as Vercel).

---

## ✅ Pre-Deployment Checklist

Before deploying, test locally:

```bash
cd apps/web
npm install
npm run build:marketing
npm run preview
```

Visit `http://localhost:4173` to verify everything works.

---

## 🎯 Custom Domain

After deployment:

**Vercel:**
- Go to Project Settings → Domains
- Add your domain (e.g., `marketing.healthforesight.com`)
- Follow DNS instructions
- SSL is automatic

**Netlify:**
- Go to Site Settings → Domain Management
- Add custom domain
- Follow DNS instructions
- SSL is automatic

---

## 📊 What Gets Deployed

- ✅ All marketing pages (Home, Platform, Solutions, How It Works, etc.)
- ✅ All visual components and animations
- ✅ All assets (images, logos, fonts)
- ✅ SEO meta tags
- ✅ Analytics ready (if configured)

---

## 🆘 Troubleshooting

**Build fails?**
```bash
cd apps/web
rm -rf node_modules package-lock.json
npm install
npm run build:marketing
```

**Routes return 404?**
- Make sure `vercel.json` or `netlify.toml` is in `apps/web/`
- Both have rewrite rules configured

**Assets not loading?**
- Check that files are in `public/` folder
- Verify paths are relative (not absolute)

---

## 🎉 You're All Set!

Once deployed, your marketing website will be:
- ✅ Live and accessible worldwide
- ✅ Fast (CDN included)
- ✅ Secure (SSL automatic)
- ✅ Auto-updating (on every git push)

**Need help?** Check `DEPLOY_MARKETING_WEBSITE.md` for detailed instructions.
