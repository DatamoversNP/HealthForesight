# HealthForesight Website - Quick Setup Guide

## 🚀 Quick Start (For Cursor or Any Editor)

### 1. Navigate to Website Folder

```bash
cd healthforesight-Website
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

The website will be available at `http://localhost:3052` (or next available port)

---

## 📦 Build for Production

```bash
npm run build
```

Output will be in `dist/` folder.

---

## 🌐 Deploy to Vercel

```bash
# From healthforesight-Website directory
npx vercel --prod
```

Or connect to Vercel dashboard and deploy from GitHub.

---

## 📁 Project Structure

```
healthforesight-Website/
├── public/              # Static assets (logos, etc.)
├── src/
│   ├── pages/          # All marketing pages
│   ├── components/     # All marketing components
│   ├── theme/          # Theme configuration
│   ├── App.tsx         # Main app (routes)
│   └── main.tsx        # Entry point
├── index.html
├── package.json
├── vite.config.ts
└── vercel.json         # Deployment config
```

---

## ✅ Checklist Before Deployment

- [ ] Logo files in `public/` folder ✅
- [ ] All import paths updated (relative) ✅
- [ ] Dependencies installed (`npm install`) ✅
- [ ] Dev server runs without errors ✅
- [ ] Build succeeds (`npm run build`) ✅

---

## 🛠️ Common Commands

```bash
# Development
npm run dev              # Start dev server

# Production
npm run build            # Build for production
npm run preview          # Preview production build

# Deployment
npx vercel --prod        # Deploy to Vercel
```

---

## 📝 Notes

- **Standalone**: This website is completely independent of the core application
- **Port**: Defaults to 3052, but will use next available if busy
- **Routing**: All routing handled by React Router (client-side)
- **Assets**: Files in `public/` are served at root path (`/logo.svg`)

---

## 🔧 Troubleshooting

### Logo not loading?
- Check `public/healthforesight-logo.svg` exists
- Restart dev server
- Hard refresh browser (`Cmd+Shift+R`)

### Import errors?
- All imports should be relative paths
- Check `src/theme/healthForesightTheme.ts` exists
- Verify component imports use `../components/` not `../components/marketing/`

### Port already in use?
- Vite will automatically try next available port
- Or change port in `vite.config.ts`

---

## 📚 Documentation

- `README.md` - Project overview
- `MIGRATION_GUIDE.md` - How files were migrated
- `QUICK_START.md` - Navigation help
- `SEPARATION_COMPLETE.md` - Setup status

---

**Ready to use!** Just run `npm install && npm run dev`
