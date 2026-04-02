# If `git push -f origin main` fails with HTTP 400

Git’s default HTTP buffer can be too small and cause “400” or “remote end hung up” even when the repo is only a few MB.

## 1. Increase the HTTP post buffer (try this first)

```bash
git config http.postBuffer 524288000
git push -f origin main
```

(524288000 = 500 MB; the whole pack is sent in one request.)

## 2. If it still fails: push without Vite cache

Build cache under `apps/web/.vite/` is large. Remove it from the last commit and push again:

```bash
git rm -r --cached apps/web/.vite 2>/dev/null || true
git commit --amend -m "healthforesight v3" --no-edit
git push -f origin main
```

`.vite/` is in `.gitignore` so it won’t be re-added.
