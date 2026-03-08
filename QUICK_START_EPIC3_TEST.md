# Quick Start: Epic 3 UI Testing

## 🚀 One-Command Start

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./START_EPIC3_TESTING.sh
```

This will:
- ✅ Start API server on port 8000
- ✅ Start frontend on port 3050
- ✅ Show you next steps

## 📋 Quick Test Steps

1. **Open Browser**: http://localhost:3050

2. **Navigate**: Policies → Open Workspace (on any policy)

3. **Test Decisions**:
   - Click **"Decisions"** tab (9th tab)
   - Click **"Create Decision"**
   - Fill form and create
   - ✅ Decision should appear

4. **Test Evidence**:
   - Click **"Evidence"** tab (10th tab)
   - Click **"Link Evidence"**
   - Fill form and link
   - ✅ Evidence should appear

## ✅ Success Indicators

- Decisions tab visible and working
- Evidence tab visible and working
- Can create decisions
- Can link evidence
- No errors in browser console

## 🛑 Stop Servers

```bash
lsof -ti:8000 | xargs kill
lsof -ti:3050 | xargs kill
```

---

**That's it! Start testing!** 🎉


