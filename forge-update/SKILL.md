---
name: forge-update
description: "Update Forge to the latest version and show what changed. Use on 'update forge', '/forge-update', 'is there a new forge', 'pull latest forge'."
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
---

# /forge-update — pull the latest Forge, show what changed

Forge installs as a **symlink** from `~/.claude/skills/forge` to a cloned git repo (see `install.sh`), so updating is a `git pull` in that repo and the symlink picks it up next session. This command checks the version, shows the changelog for what's new, and fast-forwards — without clobbering local edits.

## Process

1. **Find the repo.**
   - `SKILL="$HOME/.claude/skills/forge"`.
   - If `SKILL` is a symlink: `REPO="$(cd "$SKILL" && pwd -P)"` (resolve to the real clone).
   - Else if `SKILL/.git` or `SKILL` is itself a git repo: `REPO="$SKILL"`.
   - Else: tell the user Forge wasn't installed via `install.sh` (no repo to pull) and stop, pointing them to `git pull` in wherever they cloned it.

2. **Fetch and compare.** In `REPO`:
   - `git fetch --quiet origin` (if this fails — offline / no remote — say so and stop gracefully).
   - Local version: `cat VERSION`. Upstream: `git show origin/main:VERSION`.
   - Commits behind: `git rev-list --count HEAD..origin/main`.

3. **If up to date** (behind = 0): print `✅ Forge is up to date (vX.Y.Z).` and stop.

4. **If behind, show what's new.** Print the current → new version, then the changelog entries newer than the local version: `git show origin/main:CHANGELOG.md` and display the sections above the installed version. Keep it to the `Added` / `Fixed` bullets, not the whole file.

5. **Confirm, then update.** Ask the user to confirm (AskUserQuestion or a printed `[Y/n]`). On yes:
   - If the working tree is clean: `git pull --ff-only origin main`.
   - If it **can't fast-forward or the tree is dirty** (the user customized their copy): do NOT force. Show `git status`, explain their copy diverged from upstream, and offer the options — `git stash` then pull then `git stash pop`, or review the diff first. Never overwrite local changes silently. (A future release will do a three-way reapply-merge like GSD's `--reapply`.)

6. **Confirm result.** Print the new version and note that a symlink install needs nothing further — Claude Code loads the updated skill next session. Remind them to restart the session to pick it up.

## Rules
- Read-only until the user confirms the pull. Never `git reset --hard` or force-overwrite.
- Offline, detached HEAD, or a non-`origin/main` setup → report the situation and stop; don't guess.
- This updates the public/distributed copy. Maintainers who keep a separate live copy sync that themselves.
