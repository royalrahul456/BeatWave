# LiquidGlass AI Agent Skill

https://github.com/user-attachments/assets/3cb9c731-5b5f-4726-9866-d704fd167ff0

Universal AI agent skill for implementing realistic WebGL liquid glass refraction, blur, chromatic aberration, and lighting effects using [`@ybouane/liquidglass`](https://github.com/ybouane/liquidglass) ([Live Demo](https://liquid-glass.ybouane.com/)).

Compatible with:
- **GitHub Copilot (`.github/skills/`)**
- **Google Antigravity & Antigravity CLI (`agy`)**
- **Anthropic Claude Code (`claude`)**
- **OpenAI Codex CLI & ChatGPT (`codex`)**
- **Cursor / Windsurf (`.cursorrules` / `.agents`)**
- **Universal Agent Standard (`~/.agents/skills`)**

---

## ⚡ 1-Line Quick Install

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/RmaNMetaverse/Apple-LiquidGlass-Skill/main/install.ps1 | iex
```

### macOS / Linux (Bash)
```bash
curl -fsSL https://raw.githubusercontent.com/RmaNMetaverse/Apple-LiquidGlass-Skill/main/install.sh | bash
```

---

## 📂 Installation Directories

| Agent | Global Directory | Project-Level Directory |
| :--- | :--- | :--- |
| **GitHub Copilot** | `.github/skills/liquidglass/` | `.github/skills/liquidglass/` |
| **Antigravity / Gemini** | `~/.gemini/config/skills/liquidglass/` | `.agents/skills/liquidglass/` |
| **Claude Code** | `~/.claude/skills/liquidglass/` | `.claude/skills/liquidglass/` |
| **ChatGPT / Codex** | `~/.codex/skills/liquidglass/` | `.codex/skills/liquidglass/` |
| **Universal Agents** | `~/.agents/skills/liquidglass/` | `.agents/skills/liquidglass/` |

---

## 🛠️ Verification Checklist

- [x] **Metadata**: Valid YAML frontmatter in `SKILL.md` with lowercase, single-word/hyphenated `name: liquidglass` and keyword-rich `description`.
- [x] **Structure**: Standard repository structure with `.github/skills/liquidglass/SKILL.md` for GitHub Copilot and root `SKILL.md` for Claude, Codex, Antigravity, and generic agents.
- [x] **1-Line Installers**: PowerShell (`install.ps1`) and Bash (`install.sh`) scripts that support both remote execution (`irm | iex` / `curl | bash`) and local execution.
