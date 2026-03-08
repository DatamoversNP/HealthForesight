#!/usr/bin/env bash
# Push a single-commit "clean" history to GitHub to avoid 1.8GB push from large files in history.
# Run from repo root: ./scripts/push_clean_to_github.sh
# This replaces remote 'main' with one commit containing only code (no data/zips/backups).
# Note: Your local full history remains in reflog until pruned; only the branch name 'main' is replaced.

set -e
cd "$(dirname "$0")/.."

echo "=== Creating clean single-commit history for GitHub ==="
echo "Large paths (apps/data, *.zip, backups, etc.) are in .gitignore and will not be in the commit."
echo "Current .git size: $(du -sh .git 2>/dev/null | cut -f1)"
echo ""

# Create orphan branch (no parent = no history)
git checkout --orphan main-clean
# Unstage everything so we re-add only what .gitignore allows
git reset
git add -A
FILE_COUNT=$(git status --short | wc -l | tr -d ' ')
echo "Staged $FILE_COUNT paths (large data/zips excluded by .gitignore)"
git status --short | head -20
echo "..."
echo ""

git commit -m "healthforesight v3"
echo ""

# Replace main with this branch
git branch -D main 2>/dev/null || true
git branch -m main

echo "=== Done. Push with: ==="
echo "  git push -f origin main"
echo ""
echo "This will replace the remote main with this single commit (no large files)."
