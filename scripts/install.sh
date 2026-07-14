#!/usr/bin/env bash
# install.sh — One-click install patent-disclosure-skill for current platform
#
# Detects available AI coding tools and installs the skill to the correct path.
# Supports: Codex, opencode, Claude Code, Cursor
#
# Usage:
#   bash scripts/install.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== patent-disclosure-skill Installer ==="
echo "Source: $REPO_DIR"
echo ""

# --- Detect platform ---
install_codex() {
  local target="$HOME/.agents/skills/patent-disclosure-skill"
  echo "[Codex] Installing to $target"
  mkdir -p "$HOME/.agents/skills"
  if [ -d "$target" ]; then
    echo "  → Already installed. Updating symlink."
    rm -f "$target"
  fi
  ln -sf "$REPO_DIR" "$target"
  echo "  ✓ Done. Restart Codex to discover the skill."
}

install_opencode() {
  local target="$HOME/.config/opencode/skills/patent-disclosure-skill"
  echo "[opencode] Installing to $target"
  mkdir -p "$HOME/.config/opencode/skills"
  if [ -d "$target" ]; then
    echo "  → Already installed. Updating symlink."
    rm -f "$target"
  fi
  ln -sf "$REPO_DIR" "$target"
  echo "  ✓ Done. Restart opencode to discover the skill."
}

install_claude() {
  local target="$HOME/.claude/skills/patent-disclosure-skill"
  echo "[Claude Code] Installing to $target"
  mkdir -p "$HOME/.claude/skills"
  if [ -d "$target" ]; then
    echo "  → Already installed. Updating symlink."
    rm -f "$target"
  fi
  ln -sf "$REPO_DIR" "$target"
  echo "  ✓ Done. Restart Claude Code to discover the skill."
}

install_cursor() {
  local target="$HOME/.cursor/skills/patent-disclosure-skill"
  echo "[Cursor] Installing to $target"
  mkdir -p "$HOME/.cursor/skills"
  if [ -d "$target" ]; then
    echo "  → Already installed. Updating symlink."
    rm -f "$target"
  fi
  ln -sf "$REPO_DIR" "$target"
  echo "  ✓ Done. Restart Cursor to discover the skill."
}

# --- Try to detect and install ---
installed=false

if command -v codex &>/dev/null; then
  install_codex
  installed=true
fi

if command -v opencode &>/dev/null; then
  install_opencode
  installed=true
fi

if [ -n "${CLAUDE_CODE:-}" ] || command -v claude &>/dev/null; then
  install_claude
  installed=true
fi

if [ -d "$HOME/.cursor" ]; then
  install_cursor
  installed=true
fi

if [ "$installed" = false ]; then
  echo "No supported AI coding tool detected."
  echo "Install manually: see INSTALL.md, .codex/INSTALL.md, .opencode/INSTALL.md"
  exit 1
fi

echo ""
echo "=== Installation complete ==="
