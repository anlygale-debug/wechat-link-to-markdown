#!/bin/bash
set -euo pipefail

PACKAGE_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$PACKAGE_DIR/skill/wechat-link-to-markdown"
if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
  REPOSITORY_ROOT="$(cd "$PACKAGE_DIR/.." && pwd)"
  SOURCE_DIR="$REPOSITORY_ROOT/skill/wechat-link-to-markdown"
fi
SKILLS_DIR="$HOME/.agents/skills"
TARGET_DIR="$SKILLS_DIR/wechat-link-to-markdown"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This installer is for macOS."
  exit 1
fi

for command_name in node npm python3; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing dependency: $command_name"
    echo "Install Node.js 20+ and Python 3.10+, then run this installer again."
    exit 2
  fi
done

if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
  echo "Skill files are missing from: $SOURCE_DIR"
  exit 3
fi

echo "Installing OpenCLI 1.8.7..."
npm install -g @jackwener/opencli@1.8.7

mkdir -p "$SKILLS_DIR"
if [ -e "$TARGET_DIR" ]; then
  BACKUP_DIR="$TARGET_DIR.backup-$(date +%Y%m%d-%H%M%S)"
  echo "Existing skill found. Backing it up to: $BACKUP_DIR"
  mv "$TARGET_DIR" "$BACKUP_DIR"
fi

cp -R "$SOURCE_DIR" "$TARGET_DIR"

echo
echo "Skill installed at: $TARGET_DIR"
echo "Next steps:"
echo "1. Install and enable the OpenCLI Chrome extension:"
echo "   https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk"
echo "2. Keep Chrome open and run: opencli doctor"
echo "3. Restart Codex only if the skill does not appear automatically."
