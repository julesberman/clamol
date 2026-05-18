#!/usr/bin/env bash
# clamol installer — one-time per machine.
# Idempotent: re-running is safe. Each step is opt-in.

set -euo pipefail

# ─── colors ────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  B=$'\033[1m'; D=$'\033[2m'; R=$'\033[0m'
  G=$'\033[32m'; Y=$'\033[33m'; RD=$'\033[31m'; C=$'\033[36m'; M=$'\033[35m'
else
  B=''; D=''; R=''; G=''; Y=''; RD=''; C=''; M=''
fi

# ─── paths ─────────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$REPO_ROOT/skills/pymol"
SKILL_DST="$HOME/.claude/skills/pymol"
VENV="$REPO_ROOT/.venv"
CLAMOL_BIN="$VENV/bin/clamol"
LAUNCHER_BIN="$VENV/bin/clamol-launch-pymol"
BIN_DIR="$HOME/.local/bin"

# ─── flags ─────────────────────────────────────────────────────────────────
ASSUME_YES=0
for arg in "$@"; do
  case "$arg" in
    -y|--yes) ASSUME_YES=1 ;;
    -h|--help)
      cat <<EOF
Usage: bash install.sh [-y]

Installs clamol in three steps (each prompted unless -y):
  1. Create a Python venv and install clamol editable into it.
  2. Symlink the pymol skill into ~/.claude/skills/.
  3. Register clamol as a user-scope MCP server in Claude Code.

Re-runs are idempotent. Pass -y/--yes for non-interactive install.
EOF
      exit 0
      ;;
  esac
done

# ─── ui helpers ────────────────────────────────────────────────────────────
hr() { printf '%s%s%s\n' "$D" "──────────────────────────────────────────────────────────────" "$R"; }

banner() {
  echo
  printf '%s   ╔══════════════════════════════════════════════════════════╗%s\n' "$B$C" "$R"
  printf '%s   ║                  clamol installer                        ║%s\n' "$B$C" "$R"
  printf '%s   ╚══════════════════════════════════════════════════════════╝%s\n' "$B$C" "$R"
  echo
}

section() {
  echo
  printf '%s▌ %s%s\n' "$B$M" "$1" "$R"
  hr
}

why()  { printf '  %s%s%s\n' "$D" "$1" "$R"; }
note() { printf '  %s\n' "$1"; }
ok()   { printf '  %s✓%s %s\n' "$G" "$R" "$1"; }
warn() { printf '  %s⚠%s %s\n' "$Y" "$R" "$1"; }
fail() { printf '  %s✗%s %s\n' "$RD" "$R" "$1"; }
run()  { printf '  %s$%s %s\n' "$D" "$R" "$1"; }

ask() {
  # ask "prompt" [Y|n]   -> returns 0 for yes, 1 for no
  local prompt="$1" default="${2:-Y}" hint reply
  [[ $default == Y ]] && hint="[${B}Y${R}/n]" || hint="[y/${B}N${R}]"
  if (( ASSUME_YES )); then
    printf '  %s?%s %s %s %s(assumed yes)%s\n' "$B" "$R" "$prompt" "$hint" "$D" "$R"
    return 0
  fi
  printf '  %s?%s %s %s ' "$B" "$R" "$prompt" "$hint"
  read -r reply </dev/tty || reply=""
  reply="${reply:-$default}"
  [[ $reply =~ ^[Yy]$ ]]
}

# ─── start ─────────────────────────────────────────────────────────────────
banner
note "${B}This installer does three things:${R}"
note "  ${B}1.${R} Create a Python venv with clamol installed editable"
note "  ${B}2.${R} Symlink the ${C}pymol skill${R} so Claude Code auto-loads it"
note "  ${B}3.${R} Register clamol as a ${C}user-scope MCP server${R} in Claude Code"
echo
why  "After this, every \`claude\` session in every directory on this machine"
why  "can use the pymol tools — no per-project .mcp.json needed."
echo
why  "Detected repo: $REPO_ROOT"

# ─── prereq check ──────────────────────────────────────────────────────────
section "Prerequisites"

if command -v python3 >/dev/null; then
  ok "python3:   $(python3 --version 2>&1)"
else
  fail "python3 not on PATH. Install Python 3.11+ and re-run."
  exit 1
fi

if command -v claude >/dev/null; then
  ok "claude:    $(command -v claude)"
else
  fail "claude CLI not on PATH. Install Claude Code first."
  exit 1
fi

if command -v pymol >/dev/null; then
  ok "pymol:     $(command -v pymol)"
else
  warn "pymol not on PATH. Install with ${B}brew install pymol${R} (or conda)."
  why  "  Skill + MCP install still works; tools will error until pymol is installed."
fi

# ─── step 1: venv ──────────────────────────────────────────────────────────
section "Step 1 — Python venv + editable install"
why  "Creates $VENV, runs \`pip install -e .\`, and symlinks the \`clamol\` and"
why  "\`clamol-launch-pymol\` console scripts into $BIN_DIR so they're on \$PATH."

if [[ -x $CLAMOL_BIN ]]; then
  ok "venv already exists at $VENV — skipping create"
elif ask "Create venv and install clamol?" "Y"; then
  run "python3 -m venv $VENV"
  python3 -m venv "$VENV"
  run "$VENV/bin/pip install -e $REPO_ROOT"
  "$VENV/bin/pip" install --quiet -e "$REPO_ROOT"
  ok "venv ready: $CLAMOL_BIN"
else
  warn "skipped — later steps will fail without a clamol binary"
fi

# Symlink console scripts onto PATH so `clamol-launch-pymol` is reachable
# from anywhere — not just when the venv is activated.
if [[ -x $CLAMOL_BIN ]]; then
  link_needed=0
  for src in "$CLAMOL_BIN" "$LAUNCHER_BIN"; do
    name="$(basename "$src")"
    dst="$BIN_DIR/$name"
    if [[ -L $dst && "$(readlink "$dst")" == "$src" ]]; then
      continue
    fi
    link_needed=1; break
  done
  if (( link_needed )); then
    if ask "Symlink console scripts into $BIN_DIR?" "Y"; then
      mkdir -p "$BIN_DIR"
      for src in "$CLAMOL_BIN" "$LAUNCHER_BIN"; do
        name="$(basename "$src")"
        dst="$BIN_DIR/$name"
        run "ln -sfn $src $dst"
        ln -sfn "$src" "$dst"
      done
      # PATH sanity check — warn if BIN_DIR isn't on PATH
      case ":$PATH:" in
        *":$BIN_DIR:"*) ok "$BIN_DIR is on \$PATH — \`clamol-launch-pymol\` should work in any shell" ;;
        *) warn "$BIN_DIR is not on \$PATH. Add this to your shell rc:"
           note "    export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
      esac
    else
      note "skipped — invoke commands via full path: $CLAMOL_BIN"
    fi
  else
    ok "console scripts already symlinked into $BIN_DIR"
  fi
fi

# ─── step 2: skill symlink ─────────────────────────────────────────────────
section "Step 2 — install the pymol skill"
why  "Symlinks $SKILL_SRC into $SKILL_DST."
why  "Symlink (not copy) so \`git pull\` updates everyone's skill in place."

if [[ -L $SKILL_DST && "$(readlink "$SKILL_DST")" == "$SKILL_SRC" ]]; then
  ok "skill already symlinked correctly"
elif [[ -e $SKILL_DST ]]; then
  warn "$SKILL_DST exists but points elsewhere:"
  note "    $(readlink "$SKILL_DST" 2>/dev/null || echo "(not a symlink)")"
  if ask "Replace it with a link to this repo?" "N"; then
    run "rm -rf $SKILL_DST && ln -s $SKILL_SRC $SKILL_DST"
    rm -rf "$SKILL_DST"
    mkdir -p "$(dirname "$SKILL_DST")"
    ln -s "$SKILL_SRC" "$SKILL_DST"
    ok "skill linked"
  else
    note "skipped"
  fi
elif ask "Install the skill?" "Y"; then
  run "mkdir -p $(dirname "$SKILL_DST") && ln -s $SKILL_SRC $SKILL_DST"
  mkdir -p "$(dirname "$SKILL_DST")"
  ln -s "$SKILL_SRC" "$SKILL_DST"
  ok "skill linked"
else
  note "skipped"
fi

# ─── step 3: MCP register ──────────────────────────────────────────────────
section "Step 3 — register MCP server (user scope)"
why  "Adds clamol to ~/.claude.json so every \`claude\` session has the"
why  "MCP tools available — no need to copy .mcp.json into each project."

if [[ ! -x $CLAMOL_BIN ]]; then
  fail "no clamol binary — skipping (rerun after step 1 succeeds)"
else
  existing="$(claude mcp list 2>/dev/null | grep -E '^clamol[: ]' || true)"
  if [[ -n $existing ]]; then
    warn "clamol is already registered:"
    note "    $existing"
    if ask "Re-register (will overwrite)?" "N"; then
      run "claude mcp remove clamol -s user"
      claude mcp remove clamol -s user >/dev/null 2>&1 || true
      run "claude mcp add clamol -s user -- $CLAMOL_BIN"
      claude mcp add clamol -s user -- "$CLAMOL_BIN"
      ok "clamol re-registered"
    else
      note "skipped"
    fi
  elif ask "Register clamol at user scope?" "Y"; then
    run "claude mcp add clamol -s user -- $CLAMOL_BIN"
    claude mcp add clamol -s user -- "$CLAMOL_BIN"
    ok "clamol registered (user scope) -> $CLAMOL_BIN"
  else
    note "skipped"
  fi
fi

# ─── done ──────────────────────────────────────────────────────────────────
section "Done"
note "Each session:"
note "  ${B}clamol-launch-pymol &${R}     ${D}# starts PyMOL with RPC on :9123${R}"
note "  ${B}claude${R}                    ${D}# in any directory — skill + tools auto-load${R}"
echo
why  "Re-run \`bash install.sh\` anytime; it's idempotent."
echo
