# Quick Start Guide

## 📍 Current Location

You're currently in: `apps/web/`

The `healthforesight-Website` folder is at the **root level** of the project.

## 🚀 Navigate & Run Migration

### Option 1: Navigate step by step

```bash
# Go to project root (2 levels up from apps/web)
cd ../..
cd healthforesight-Website
./migrate.sh
```

### Option 2: Navigate directly

```bash
# From apps/web/, go directly to healthforesight-Website
cd ../../healthforesight-Website
./migrate.sh
```

### Option 3: Run from any location

```bash
# From anywhere in the project
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution/healthforesight-Website"
./migrate.sh
```

## ✅ After Migration

```bash
# Install dependencies
npm install

# Test locally
npm run dev

# Build for production
npm run build
```

## 📂 Project Structure

```
Utilization Elastisity and Policy Impact Solution/
├── apps/
│   └── web/                    ← You are here
│       └── src/
│           ├── pages/marketing/    ← Source files
│           └── components/marketing/ ← Source files
│
└── healthforesight-Website/    ← Destination folder (root level)
    ├── migrate.sh              ← Run this script
    └── src/
        ├── pages/              ← Files will be copied here
        └── components/         ← Files will be copied here
```

## 🎯 Quick Command Reference

```bash
# From apps/web/ directory:
cd ../../healthforesight-Website && ./migrate.sh && npm install && npm run dev
```

This will:
1. Navigate to `healthforesight-Website`
2. Run migration script
3. Install dependencies
4. Start dev server

---

**Note**: Use `cd ../..` (two dots, space, two dots) to go up two directories!
