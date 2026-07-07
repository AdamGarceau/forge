#!/bin/zsh
# Forge installer — symlink the skill into ~/.claude/skills so Claude Code picks it up,
# then make sure the build engine (GSD) it depends on is present.
set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/forge"

mkdir -p "$HOME/.claude/skills"

if [[ -e "$SKILL_DIR" && ! -L "$SKILL_DIR" ]]; then
  echo "⚠️  $SKILL_DIR exists and is not a symlink."
  echo "    Back it up or remove it, then re-run. (Not touching it.)"
  exit 1
fi

ln -sfn "$REPO_DIR" "$SKILL_DIR"
echo "✅ Forge installed: $SKILL_DIR → $REPO_DIR"

# Also link Reggie's /reggie summon skill (same repo, shares scripts/reggie.py).
REGGIE_DIR="$HOME/.claude/skills/reggie"
if [[ -e "$REGGIE_DIR" && ! -L "$REGGIE_DIR" ]]; then
  echo "⚠️  $REGGIE_DIR exists and is not a symlink; skipping /reggie (back it up to enable)."
else
  ln -sfn "$REPO_DIR/reggie" "$REGGIE_DIR"
  echo "✅ /reggie installed: summon the ackchyually guy anytime."
fi

# ── Build engine: GSD (highly recommended) ────────────────────────────────────
# Forge's Stage 2 (BUILD) is far better with GSD — it's the recommended build
# engine, but NOT required: Forge falls back to a direct Claude Code build if
# it's absent. GSD is a public npm package (@opengsd/get-shit-done-redux). We
# detect it and OFFER to install it rather than pulling a second framework into
# ~/.claude silently. Set FORGE_INSTALL_GSD=1 to auto-yes, FORGE_SKIP_GSD=1 to
# skip. A failure here never fails the Forge install (Forge itself is done).
GSD_INSTALL_CMD="npx -y @opengsd/get-shit-done-redux@latest --global"

gsd_present() {
  [ -d "$HOME/.claude/get-shit-done" ] && return 0
  # `find` does the matching (glob is quoted), so this is clean under both zsh
  # (no nomatch error) and bash (no nullglob dependency) — works for `bash install.sh`.
  [ -n "$(find "$HOME/.claude/skills" -maxdepth 1 -name 'gsd-*' -print -quit 2>/dev/null)" ]
}

install_gsd() {
  set +e
  echo "   Installing GSD… ($GSD_INSTALL_CMD)"
  eval "$GSD_INSTALL_CMD"
  local rc=$?
  set -e
  if [[ $rc -eq 0 ]] && gsd_present; then
    echo "✅ GSD build engine installed."
  else
    echo "⚠️  GSD install didn't complete. Forge is installed and its validation"
    echo "    stages (0-1) + bundled synth tools work now. To enable the BUILD"
    echo "    stage later, run:  $GSD_INSTALL_CMD"
  fi
}

echo
if gsd_present; then
  echo "✅ GSD build engine detected — Forge's build stage will use it."
elif [[ -n "$FORGE_SKIP_GSD" ]]; then
  echo "ℹ️  Skipping GSD (FORGE_SKIP_GSD set). It's highly recommended for the"
  echo "    build stage — install it anytime with:  $GSD_INSTALL_CMD"
elif ! command -v npm >/dev/null 2>&1; then
  echo "ℹ️  Forge's BUILD stage is much better with GSD (a public npm package),"
  echo "    though not required — Forge can build without it."
  echo "    Node/npm wasn't found. To add GSD: install Node (https://nodejs.org), then:"
  echo "    $GSD_INSTALL_CMD"
elif [[ -n "$FORGE_INSTALL_GSD" ]]; then
  install_gsd
elif [[ -t 0 ]]; then
  echo "Forge's BUILD stage is highly recommended to run on GSD"
  echo "(public npm pkg @opengsd/get-shit-done-redux). It's optional — Forge can"
  echo "build without it, but GSD makes the build far more reliable."
  printf "Install GSD now? [Y/n] "
  read -r reply || reply=""   # EOF (Ctrl-D) → empty, not a set -e abort
  if [[ -z "$reply" || "$reply" == [Yy]* ]]; then
    install_gsd
  else
    echo "ℹ️  Skipped — Forge will use its direct build fallback. Add GSD anytime:"
    echo "    $GSD_INSTALL_CMD"
  fi
else
  # non-interactive (piped) — don't surprise-install; print the one-liner.
  echo "ℹ️  Forge's BUILD stage is highly recommended to run on GSD. Add it with:"
  echo "    $GSD_INSTALL_CMD"
  echo "    (or re-run this installer in a terminal to be prompted, or set FORGE_INSTALL_GSD=1)"
fi

echo
echo "   Start any Claude Code session and describe an app idea, or ask \"is this worth building?\""
