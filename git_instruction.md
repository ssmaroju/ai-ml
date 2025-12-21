# Git Workflow Instructions

## Initial Setup (one-time)

### 1) Create the folder
```bash
mkdir -p /c/PM/Deep/prototyping/ai-ml
cd /c/PM/Deep/prototyping/ai-ml
```

### 2) Initialize git + create first commit
```bash
git init
git branch -M main
echo "# ai-ml" > README.md
git add README.md
git commit -m "Initial commit"
```

### 3) Create a new GitHub repo (important)
- On GitHub, create a repo named `ai-ml` (or your preferred name)
- Do NOT add a README/license/gitignore on GitHub (since you already made a local commit)
- If you already created it with files, see "Handling Conflicts" section below

### 4) Connect local to GitHub and push
```bash
git remote add origin https://github.com/<your-username>/ai-ml.git
git push -u origin main
```

---

## Daily Workflow (Best Practices)

### Before Starting Work - ALWAYS Sync First

**Step 1: Fetch remote changes (doesn't modify local files)**
```bash
cd /c/PM/Deep/prototyping/ai-ml
git fetch origin
```

**Step 2: Check sync status**
```bash
git status
```

This will show one of these states:

| Status Message | Meaning | Action |
|----------------|---------|--------|
| `Your branch is up to date` | Local = Remote | Safe to work |
| `Your branch is behind by X commits` | Remote is newer | Pull first |
| `Your branch is ahead by X commits` | Local is newer | Push first |
| `Your branch has diverged` | Both changed | Rebase required |

**Step 3: Take appropriate action**

#### If Remote is Newer (pull first):
```bash
git pull --rebase origin main
```

#### If Local is Newer (push your changes):
```bash
git status                           # Review what's uncommitted
git add .                            # Stage changes
git commit -m "Descriptive message"  # Commit with clear remarks
git push origin main                 # Push to remote
```

#### If Branches Diverged (rebase):
```bash
git stash                            # Save uncommitted work
git pull --rebase origin main        # Rebase on remote
git stash pop                        # Restore your work
# Resolve any conflicts if they occur
git add .
git commit -m "Merge: resolved conflicts"
git push origin main
```

---

## Quick Reference: Start-of-Session Script

Run this every time you start working:
```bash
cd /c/PM/Deep/prototyping/ai-ml

# Fetch and check status
git fetch origin
STATUS=$(git status -sb)

if echo "$STATUS" | grep -q "behind"; then
    echo "Remote has updates. Pulling..."
    git pull --rebase origin main
elif echo "$STATUS" | grep -q "ahead"; then
    echo "Local has unpushed commits. Review and push:"
    git log origin/main..HEAD --oneline
    read -p "Push now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin main
    fi
else
    echo "Repository is in sync. Ready to work."
fi
```

---

## During Work: Checkpoint Commits

Make frequent, small commits with meaningful messages:
```bash
git status                                    # See what changed
git diff                                      # Review changes
git add <specific-files>                      # Stage specific files (preferred)
# OR
git add .                                     # Stage all changes
git commit -m "feat: add channel validation"  # Commit with clear message
```

### Commit Message Convention
Use prefixes for clarity:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code restructuring
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks

---

## End of Session: Push Your Work

Always push before ending your session:
```bash
git status                    # Verify everything is committed
git push origin main          # Push to remote
```

---

## Handling Conflicts

### If GitHub repo already has commits/files
```bash
git pull --rebase origin main
# Resolve any conflicts in your editor
git add .
git rebase --continue
git push origin main
```

### If rebase gets messy, abort and try merge instead
```bash
git rebase --abort
git pull origin main          # This creates a merge commit
git push origin main
```

---

## Prevent Accidental Nesting / Confusion

**Rule:** Only `ai-ml` has a `.git` folder.

### Check from each folder:

**From prototyping:**
```bash
cd /c/PM/Deep/prototyping
git status
```
If you see "not a git repository" → GOOD (means prototyping isn't a repo).

**From ai-ml:**
```bash
cd /c/PM/Deep/prototyping/ai-ml
git status
```
Should show branch info → GOOD.

### If you accidentally made prototyping a git repo:
- **Best:** Remove git from prototyping so only ai-ml is tracked
- **Alternative:** Keep prototyping as a repo (ai-ml becomes nested - usually annoying)

To remove git from prototyping (ONLY if you don't intend to track it):
```bash
cd /c/PM/Deep/prototyping
rm -rf .git
```
(This doesn't delete your files—just the git tracking metadata.)

---

## Suggested Starter Files (good hygiene)

### Create a .gitignore:
```bash
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
.venv/
.env
.ipynb_checkpoints/
.vscode/
.idea/
*.log
data/
outputs/
mlruns/
EOF
```

### (Optional) Add standard folders:
```bash
mkdir -p src notebooks configs tests
```

---

## Diagnostic Commands

To check your current state, run:
```bash
cd /c/PM/Deep/prototyping
ls -la
cd /c/PM/Deep/prototyping/ai-ml
git remote -v
git status
git log --oneline -5
```
