#!/bin/zsh
# forge-update-check.sh — SessionStart nudge for Forge.
# Prints ONE line to stdout iff the installed Forge is behind origin/main.
# Fast, non-blocking, and silent on ANY failure — it must never disrupt session start.

# Resolve the Forge repo from this script's own location (works for both a
# symlinked install and a maintainer's clone).
SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd -P)" || exit 0
REPO="$(cd "$SCRIPT_DIR/.." 2>/dev/null && pwd -P)" || exit 0
[ -d "$REPO/.git" ] || exit 0
cd "$REPO" 2>/dev/null || exit 0

# Portable timeout (macOS ships no `timeout` binary by default).
run_with_timeout() {
  local secs="$1"; shift
  "$@" & local pid=$!
  ( sleep "$secs"; kill -TERM "$pid" 2>/dev/null ) & local killer=$!
  wait "$pid" 2>/dev/null; local rc=$?
  kill -TERM "$killer" 2>/dev/null; wait "$killer" 2>/dev/null
  return $rc
}

# Throttle the network fetch to once per 24h. The cheap local compare below still
# runs every session, so the nudge persists until the user actually updates.
STAMP="$HOME/.claude/.forge-update-stamp"
now="$(date +%s 2>/dev/null)" || exit 0
last=0; [ -f "$STAMP" ] && last="$(cat "$STAMP" 2>/dev/null || echo 0)"
if [ $(( now - last )) -ge 86400 ]; then
  run_with_timeout 4 git fetch --quiet origin 2>/dev/null && echo "$now" > "$STAMP" 2>/dev/null
fi

behind="$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"
[ "${behind:-0}" -gt 0 ] 2>/dev/null || exit 0

local_v="$(cat VERSION 2>/dev/null | tr -d '[:space:]')"
remote_v="$(git show origin/main:VERSION 2>/dev/null | tr -d '[:space:]')"
echo "🔨 Forge update available: v${local_v:-?} → v${remote_v:-?} (${behind} commit(s) behind). Run /forge-update to pull it."
