# Push this project to GitHub (with configs, data, and predefined stuff)

Follow these steps from your machine. Replace `YOUR_GITHUB_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub username and repo name.

## 1. Create a new repo on GitHub

1. Go to [github.com/new](https://github.com/new).
2. Set **Repository name** (e.g. `uepi-migration` or `healthforesight-platform`).
3. Choose **Public** (or Private).
4. **Do not** initialize with README, .gitignore, or license (this project already has them).
5. Click **Create repository**.

## 2. Open terminal in this project folder

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
```

(Or use the path where this folder lives on your machine.)

## 3. Initialize Git and add the remote

```bash
# Initialize repo
git init

# Add your GitHub repo as remote (replace with your URL)
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git
```

If you use SSH:

```bash
git remote add origin git@github.com:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git
```

## 4. Stage everything (respects .gitignore)

```bash
git add .
```

Check what will be committed (optional):

```bash
git status
```

## 5. First commit

```bash
git commit -m "Initial commit: UEPI migration with configs, data, and predefined setup"
```

## 6. Push to GitHub

**If the new repo is empty and has no branches yet:**

```bash
git branch -M main
git push -u origin main
```

**If GitHub created a default branch (e.g. `main`) and you want to match it:**

```bash
git branch -M main
git push -u origin main
```

---

## What gets included

- **Configs:** `.github/workflows/`, `infra/`, app config files.
- **Code:** `apps/api/`, `apps/web/`, `packages/`, `scripts/`.
- **Data / predefined:** `apps/api/data/` (policies, baselines, analyses, etc.), root `data/` (unless you add it to .gitignore).
- **Docs:** `docs/`, root `*.md` files.

## What is ignored (see `.gitignore`)

- `.env` and other secret files.
- `node_modules/`, `.venv/`, `__pycache__/`.
- `*.log`, `logs/`, `api-logs/`.
- `.backup-core-product/` and backup folders.

---

## Optional: use the script

You can run the script once you’ve created the repo and set the variables at the top:

```bash
chmod +x push_to_github.sh
./push_to_github.sh
```

Edit `push_to_github.sh` first and set `GITHUB_USER` and `REPO_NAME`.
