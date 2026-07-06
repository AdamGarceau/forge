#!/bin/zsh
# Forge installer — symlink the skill into ~/.claude/skills so Claude Code picks it up.
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
echo "   Start any Claude Code session and describe an app idea, or ask \"is this worth building?\""
