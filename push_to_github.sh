#!/bin/bash
# Push this project to GitHub with configs, data, and predefined stuff.
# 1. Create a new repo on GitHub first (do not add README).
# 2. Set GITHUB_USER and REPO_NAME below, then run: ./push_to_github.sh

set -e

GITHUB_USER="YOUR_GITHUB_USERNAME"
REPO_NAME="YOUR_REPO_NAME"

if [[ "$GITHUB_USER" == "YOUR_GITHUB_USERNAME" ]] || [[ "$REPO_NAME" == "YOUR_REPO_NAME" ]]; then
  echo "Edit this script and set GITHUB_USER and REPO_NAME first."
  exit 1
fi

REMOTE="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Initializing git..."
  git init
fi

if ! git remote get-url origin > /dev/null 2>&1; then
  echo "Adding remote: $REMOTE"
  git remote add origin "$REMOTE"
else
  echo "Remote 'origin' already set. To change: git remote set-url origin $REMOTE"
fi

echo "Staging files (respects .gitignore)..."
git add .

echo "Status:"
git status --short | head -30
echo "..."

read -p "Commit and push? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[yY]$ ]]; then
  echo "Aborted. Run 'git commit' and 'git push' manually when ready."
  exit 0
fi

git commit -m "Initial commit: UEPI migration with configs, data, and predefined setup" || true
git branch -M main
git push -u origin main

echo "Done. Repo: $REMOTE"
