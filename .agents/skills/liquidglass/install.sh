#!/usr/bin/env bash
# LiquidGlass AI Agent Skill Installer for macOS / Linux
# Supports Antigravity, Claude Code, OpenAI Codex CLI, GitHub Copilot, and Universal Agent standard

set -e

SKILL_NAME="liquidglass"
REPO_OWNER="RmaNMetaverse"
REPO_NAME="Apple-LiquidGlass-Skill"
BRANCH="main"
RAW_BASE_URL="https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/$BRANCH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null || pwd)" && pwd)"

FILES=(
    "SKILL.md"
    "references/config-options.md"
    "examples/react.tsx"
    "examples/vanilla.html"
)

TARGETS=(
    "$HOME/.agents/skills/$SKILL_NAME"
    "$HOME/.claude/skills/$SKILL_NAME"
    "$HOME/.codex/skills/$SKILL_NAME"
    "$HOME/.gemini/config/skills/$SKILL_NAME"
)

echo "Installing $SKILL_NAME skill across all AI agents..."

IS_LOCAL=false
if [ -f "$SCRIPT_DIR/SKILL.md" ]; then
    IS_LOCAL=true
fi

for target in "${TARGETS[@]}"; do
    for file in "${FILES[@]}"; do
        dest_path="$target/$file"
        dest_dir="$(dirname "$dest_path")"
        mkdir -p "$dest_dir"
        
        if [ "$IS_LOCAL" = true ]; then
            src_path="$SCRIPT_DIR/$file"
            if [ -f "$src_path" ] && [ "$(realpath "$src_path" 2>/dev/null)" != "$(realpath "$dest_path" 2>/dev/null)" ]; then
                cp -f "$src_path" "$dest_path"
            fi
        else
            curl -fsSL "$RAW_BASE_URL/$file" -o "$dest_path"
        fi
    done
    echo "  [OK] Installed to $target"
done

echo "Done! LiquidGlass skill is now available in GitHub Copilot, Claude Code, ChatGPT/Codex, Antigravity, and .agents."
