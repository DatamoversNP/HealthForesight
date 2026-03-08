# Deploy HealthForesight Marketing Website

This guide will help you deploy the HealthForesight marketing website to production.

## Quick Deploy Options

### Option 1: Vercel (Recommended - Easiest & Fastest) ⚡

**Best for:** Quick deployment, automatic SSL, global CDN, zero configuration

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from project root**:
   ```bash
   cd apps/web
   vercel --prod
   ```

4. **Follow the prompts:**
   - Set up and deploy? **Yes**
   - Which scope? (Select your account)
   - Link to existing project? **No**
   - Project name: `healthforesight-marketing` (or your choice)
   - Directory: `apps/web`
   - Override settings? **No** (uses vercel.json)

5. **Your site will be live at:** `https://healthforesight-marketing.vercel.app` (or your custom domain)

**Alternative: Deploy via GitHub:**
1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import your repository
4. Set build command: `cd apps/web && npm run build:marketing`
5. Set output directory: `apps/web/dist-marketing`
6. Deploy!

---

### Option 2: Netlify (Also Great) 🚀

**Best for:** Easy deployment, form handling, serverless functions

1. **Install Netlify CLI**:
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify**:
   ```bash
   netlify login
   ```

3. **Deploy from project root**:
   ```bash
   cd apps/web
   netlify deploy --prod
   ```

4. **Follow the prompts:**
   - Create & configure a new site? **Yes**
   - Team: (Select your team)
   - Site name: `healthforesight-marketing` (or your choice)
   - Publish directory: `dist-marketing`

**Alternative: Deploy via GitHub:**
1. Push your code to GitHub
2. Go to [netlify.com](https://netlify.com)
3. Click "Add new site" → "Import an existing project"
4. Connect your GitHub repository
5. Build settings:
   - Build command: `cd apps/web && npm run build:marketing`
   - Publish directory: `apps/web/dist-marketing`
6. Deploy!

---

### Option 3: GitHub Pages (Free but Manual) 📄

**Best for:** Free hosting, simple static sites

1. **Build the site**:
   ```bash
   cd apps/web
   npm run build:marketing
   ```

2. **Push dist-marketing to gh-pages branch**:
   ```bash
   # From project root
   git subtree push --prefix apps/web/dist-marketing origin gh-pages
   ```

3. **Enable GitHub Pages**:
   - Go to your repository settings
   - Navigate to "Pages"
   - Source: Deploy from a branch
   - Branch: `gh-pages` / `/(root)`
   - Save

4. **Your site will be at:** `https://[username].github.io/[repo-name]`

---

### Option 4: AWS S3 + CloudFront (Enterprise) ☁️

**Best for:** Enterprise scale, custom domain, AWS integration

1. **Build the site**:
   ```bash
   cd apps/web
   npm run build:marketing
   ```

2. **Create S3 bucket** (via AWS Console or CLI):
   ```bash
   aws s3 mb s3://healthforesight-marketing --region us-east-1
   ```

3. **Enable static website hosting**:
   ```bash
   aws s3 website s3://healthforesight-marketing \
     --index-document index.html \
     --error-document index.html
   ```

4. **Upload files**:
   ```bash
   aws s3 sync apps/web/dist-marketing s3://healthforesight-marketing \
     --delete \
     --cache-control "public, max-age=31536000, immutable" \
     --exclude "*.html" \
     --exclude "*.json"
   
   aws s3 sync apps/web/dist-marketing s3://healthforesight-marketing \
     --delete \
     --cache-control "public, max-age=0, must-revalidate" \
     --include "*.html" \
     --include "*.json"
   ```

5. **Set bucket policy** (make it public):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::healthforesight-marketing/*"
       }
     ]
   }
   ```

6. **Optional: Set up CloudFront** for CDN and custom domain

---

## Pre-Deployment Checklist

Before deploying, make sure:

- [ ] Build works locally: `cd apps/web && npm run build:marketing`
- [ ] All assets load correctly (check `dist-marketing` folder)
- [ ] All routes work (test navigation)
- [ ] Environment variables are set (if any)
- [ ] Logo and images are in `public` folder
- [ ] No console errors in production build

---

## Testing the Build Locally

Before deploying, test the production build:

```bash
cd apps/web
npm run build:marketing
npm run preview
```

Visit `http://localhost:4173` to test the production build.

---

## Custom Domain Setup

### Vercel:
1. Go to your project settings → Domains
2. Add your domain (e.g., `marketing.healthforesight.com`)
3. Follow DNS instructions (add CNAME or A record)
4. SSL certificate is automatic

### Netlify:
1. Go to Site settings → Domain management
2. Add custom domain
3. Follow DNS instructions
4. SSL certificate is automatic

---

## Environment Variables (if needed)

If you need environment variables:

**Vercel:**
- Project Settings → Environment Variables
- Add variables for Production, Preview, Development

**Netlify:**
- Site settings → Environment variables
- Add variables

---

## Continuous Deployment

Both Vercel and Netlify support automatic deployments:

- **Vercel:** Automatically deploys on every push to main branch
- **Netlify:** Automatically deploys on every push to main branch

Just connect your GitHub repository and it's automatic!

---

## Troubleshooting

### Build fails:
- Check Node.js version (should be 18+)
- Run `npm install` in `apps/web`
- Check for TypeScript errors: `npm run build:marketing`

### Routes return 404:
- Make sure rewrite rules are configured (already in vercel.json/netlify.toml)
- All routes should redirect to `index.html` for client-side routing

### Assets not loading:
- Check that assets are in `public` folder
- Verify asset paths are relative (not absolute)
- Check browser console for 404 errors

### Performance issues:
- Enable compression (automatic on Vercel/Netlify)
- Check image sizes and formats
- Enable caching headers (already configured)

---

## Recommended: Vercel

**Why Vercel is recommended:**
- ✅ Zero configuration needed
- ✅ Automatic SSL certificates
- ✅ Global CDN included
- ✅ Instant deployments
- ✅ Preview deployments for PRs
- ✅ Analytics included
- ✅ Free tier is generous

**Quick start:**
```bash
cd apps/web
npm install -g vercel
vercel login
vercel --prod
```

That's it! Your site will be live in ~2 minutes.

---

## Need Help?

If you encounter any issues:
1. Check the build logs in your hosting platform
2. Test the build locally first
3. Check browser console for errors
4. Verify all dependencies are installed

Good luck! 🚀
