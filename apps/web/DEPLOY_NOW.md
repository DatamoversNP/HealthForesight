# Deploy Marketing Website to Vercel - Quick Guide

## ✅ Pre-Deployment Checklist

- [x] All responsive fixes applied
- [x] Visual components sized correctly
- [x] Buttons have touch targets (minHeight: 44)
- [x] Typography has max-width (65ch) for long-form content
- [x] `vercel.json` configured correctly
- [x] Build script configured (`build:marketing`)

## 🚀 Deploy Steps

### Option 1: Deploy via Vercel CLI (Recommended)

1. **Navigate to the web directory:**
   ```bash
   cd apps/web
   ```

2. **Deploy to production:**
   ```bash
   npx vercel --prod
   ```

3. **Follow prompts:**
   - Link to existing project? (If you've deployed before, say Yes)
   - Project name: `healthforesight-marketing` (or your preferred name)
   - Directory: `apps/web` or `.` (if already in apps/web)
   - Override settings? **No** (uses `vercel.json`)

### Option 2: Deploy via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Import your repository (or link existing project)
3. Configure:
   - **Root Directory:** `apps/web`
   - **Build Command:** `npm run build:marketing`
   - **Output Directory:** `dist-marketing`
   - **Install Command:** `npm install`
4. Click **Deploy**

## 📋 Vercel Configuration

The `vercel.json` file is already configured with:
- ✅ Build command: `npm run build:marketing`
- ✅ Output directory: `dist-marketing`
- ✅ Client-side routing rewrites
- ✅ Security headers
- ✅ Asset caching

## 🔍 Verify Deployment

After deployment, check:

1. **Homepage loads:** `https://your-project.vercel.app/`
2. **All pages work:**
   - `/platform`
   - `/solutions`
   - `/how-it-works`
   - `/who-its-for`
   - `/insights`
   - `/insights/measuring-elasticity`
   - `/insights/why-policies-backfire`
   - `/insights/cost-of-policy-uncertainty`

3. **Responsive design works:**
   - Test on mobile (375px)
   - Test on tablet (768px)
   - Test on desktop (1920px)

4. **Visuals display correctly:**
   - No text overflow
   - Proper sizing and alignment
   - Animations work

## 🐛 Troubleshooting

### Build fails
- Check Node version (Vercel uses Node 18+ by default)
- Verify `package.json` has correct build script
- Check `vercel.json` configuration

### 404 errors on routes
- Verify `rewrites` in `vercel.json` point to `/index.html`
- Ensure `dist-marketing/index.html` exists after build

### Visuals not displaying
- Check browser console for errors
- Verify assets are being served from `/assets/` directory
- Clear browser cache

## 📝 Notes

- The build automatically renames `index-marketing.html` to `index.html`
- All routing is handled client-side by React Router
- Assets are cached for 1 year (immutable)
- Security headers are applied automatically

---

**Ready to deploy!** Run `npx vercel --prod` from `apps/web` directory.
