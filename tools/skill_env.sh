#!/usr/bin/env bash
# skill_env.sh — Universal path detection for patent-disclosure-skill
#
# Detects the skill root directory across Codex, Claude Code, opencode,
# and standalone usage. Source this file in shell scripts to set SKILL_DIR.
#
# Usage:
#   source "$(dirname "$0")/skill_env.sh"
#   echo "SKILL_DIR=$SKILL_DIR"

set -euo pipefail

if [ -n "${SKILL_DIR:-}" ]; then
  # Already set — respect the existing value
  :
elif [ -n "${CODEX_SKILL_DIR:-}" ]; then
  SKILL_DIR="$CODEX_SKILL_DIR"
elif [ -n "${CLAUDE_SKILL_DIR:-}" ]; then
  SKILL_DIR="$CLAUDE_SKILL_DIR"
else
  # Fallback: resolve from script location (tools/skill_env.sh → skill root)
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

export SKILL_DIR
