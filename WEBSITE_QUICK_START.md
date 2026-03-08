# HealthForesight Website - Quick Start Guide

## 📍 Location

The standalone marketing website is in:
```
healthforesight-Website/
```

This folder is at the **root level** of the project (same level as `apps/`, `packages/`, etc.)

---

## 🚀 Quick Setup (For Cursor)

### Option 1: Automated Setup

```bash
cd healthforesight-Website
chmod +x reload.sh
./reload.sh
npm run dev
```

### Option 2: Manual Setup

```bash
# Navigate to website folder
cd healthforesight-Website

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

---

## 📦 What's Included

The `healthforesight-Website` folder is **completely standalone**:
- ✅ All marketing pages and components
- ✅ Theme configuration
- ✅ All dependencies (`package.json`)
- ✅ Vite configuration
- ✅ Deployment config (`vercel.json`)
- ✅ Logo files (`public/`)

**No dependency on core application code!**

---

## 🔄 Reloading in Cursor

1. **Open the folder**: Open `healthforesight-Website` as a workspace folder in Cursor
2. **Install dependencies**: `npm install` (if `node_modules` missing)
3. **Start dev server**: `npm run dev`
4. **Open browser**: `http://localhost:3052`

---

## 📝 Key Files

| File | Purpose |
|------|---------|
| `package.json` | Dependencies and scripts |
| `vite.config.ts` | Build configuration |
| `src/App.tsx` | Main app with routes |
| `src/main.tsx` | Entry point |
| `index.html` | HTML template |
| `vercel.json` | Deployment config |

---

## 🛠️ Common Commands

```bash
# Development
npm run dev              # Start dev server on port 3052

# Production
npm run build            # Build for production
npm run preview          # Preview production build

# Deployment
npx vercel --prod        # Deploy to Vercel
```

---

## ✅ Pre-Deployment Checklist

- [x] All files copied and imports updated
- [x] Logo files in `public/` folder
- [x] Dependencies installed
- [x] Dev server runs without errors
- [ ] Build tested (`npm run build`)
- [ ] Production preview tested (`npm run preview`)

---

## 📚 Documentation

Inside `healthforesight-Website/`:
- `SETUP.md` - Detailed setup guide
- `README.md` - Project overview
- `reload.sh` - Quick setup script
- `MIGRATION_GUIDE.md` - Migration details

---

## 🔧 Troubleshooting

### "Logo not loading"
- ✅ Logo files are in `public/` folder
- Restart dev server after adding files
- Hard refresh browser (`Cmd+Shift+R`)

### "Import errors"
- ✅ All imports are relative paths
- ✅ Theme is at `src/theme/`
- ✅ Components are at `src/components/`

### "Port in use"
- Vite automatically tries next available port
- Check terminal output for actual port number

---

## 💾 Backup

A backup was created at project root:
```
healthforesight-Website-backup-YYYYMMDD.tar.gz
```

To restore:
```bash
tar -xzf healthforesight-Website-backup-YYYYMMDD.tar.gz
```

---

**Ready to develop!** Open `healthforesight-Website` in Cursor and start coding.
