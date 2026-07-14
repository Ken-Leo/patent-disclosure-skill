#!/usr/bin/env bash
# build_disclosure.sh — Generate a formatted DOCX from a patent disclosure Markdown
#
# Uses the reference example's styles/theme/formatting to produce a Word document
# that matches the reference format exactly.
#
# Prerequisites:
#   - dotnet SDK 8.0+
#   - python-docx (pip install python-docx or via conda)
#
# Usage:
#   bash tools/minimax-docx/build_disclosure.sh \
#     --markdown "path/to/disclosure.md" \
#     --output "path/to/output.docx"
#     [--template "path/to/reference-example.docx"]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE_DEFAULT="$SKILL_DIR/examples/参考示例--一种光盘数据读取过程中的回读信号样本序列检测方法.docx"

# --- Find a working Python with python-docx ---
find_python() {
  # Try conda first
  for cand in \
    "/opt/homebrew/Caskroom/miniforge/base/bin/python3" \
    "/opt/homebrew/Caskroom/miniforge/base/bin/python" \
    "$HOME/miniforge3/bin/python3" \
    "$HOME/miniconda3/bin/python3" \
    "$HOME/anaconda3/bin/python3"; do
    if [ -f "$cand" ] && "$cand" -c "import docx" 2>/dev/null; then
      echo "$cand"
      return 0
    fi
  done
  # Try system python with user install
  if python3 -c "import docx" 2>/dev/null; then
    echo "python3"
    return 0
  fi
  # Try pip-installed
  if python3 -c "import sys; sys.path.insert(0, \"$HOME/Library/Python/3.13/lib/python/site-packages\"); import docx" 2>/dev/null; then
    echo "python3"
    return 0
  fi
  return 1
}

PYTHON=$(find_python) || {
  echo "Error: python-docx not found. Install: pip install python-docx" >&2
  exit 1
}

echo "Using Python: $PYTHON ($($PYTHON --version 2>&1))"

# --- Parse args ---
MARKDOWN=""
TEMPLATE="$TEMPLATE_DEFAULT"
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --markdown|-m) MARKDOWN="$2"; shift 2 ;;
    --template|-t) TEMPLATE="$2"; shift 2 ;;
    --output|-o) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [ -z "$MARKDOWN" ] || [ -z "$OUTPUT" ]; then
  echo "Usage: $0 --markdown FILE.md --output FILE.docx [--template FILE.docx]"
  exit 1
fi

# Resolve absolute paths
MARKDOWN_ABS="$(cd "$(dirname "$MARKDOWN")" && pwd)/$(basename "$MARKDOWN")"
OUTPUT_ABS="$(cd "$(dirname "$OUTPUT")" && pwd)/$(basename "$OUTPUT")"
TEMPLATE_ABS="$(cd "$(dirname "$TEMPLATE")" && pwd)/$(basename "$TEMPLATE")"

for f in "$MARKDOWN_ABS" "$TEMPLATE_ABS"; do
  [ -f "$f" ] || { echo "Error: file not found: $f"; exit 1; }
done

echo "=== Build Disclosure DOCX ==="
echo "  Markdown:  $MARKDOWN_ABS"
echo "  Template:  $TEMPLATE_ABS"
echo "  Output:    $OUTPUT_ABS"
echo ""

# Step 1: Build dotnet project (if not already built)
if [ ! -f "$SCRIPT_DIR/scripts/dotnet/MiniMaxAIDocx.Cli/Program.cs" ]; then
  echo "Error: minimax-docx CLI not found at $SCRIPT_DIR/scripts/dotnet"
  echo "Falling back to md_to_docx.py..."
  exec "$PYTHON" "$SKILL_DIR/tools/md_to_docx.py" -i "$MARKDOWN_ABS" -o "$OUTPUT_ABS"
fi

# Step 2: Create intermediate basic DOCX from Markdown
TMPDIR="$(mktemp -d)"
trap "rm -rf '$TMPDIR'" EXIT
BASIC_DOCX="$TMPDIR/basic.docx"

echo "[1/2] Creating basic DOCX from markdown..."
"$PYTHON" "$SKILL_DIR/tools/md_to_docx.py" -i "$MARKDOWN_ABS" -o "$BASIC_DOCX" --no-math-render 2>&1

# Step 3: Apply template styles with style mapping
echo "[2/2] Applying template styles from reference example..."
"$PYTHON" "$SCRIPT_DIR/apply_reference_style.py" \
  --input "$BASIC_DOCX" \
  --template "$TEMPLATE_ABS" \
  --output "$OUTPUT_ABS"

echo ""
echo "=== Done: $OUTPUT_ABS ==="
