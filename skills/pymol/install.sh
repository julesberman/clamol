#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.claude/skills"
ln -sfn "$HERE" "$HOME/.claude/skills/pymol"
echo "Installed pymol skill -> $HOME/.claude/skills/pymol"
echo "Restart Claude Code for the skill to be picked up."
