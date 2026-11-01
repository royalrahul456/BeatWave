# LiquidGlass AI Agent Skill Installer for Windows
# Supports Antigravity, Claude Code, OpenAI Codex CLI, GitHub Copilot, and Universal Agent standard

$ErrorActionPreference = "Stop"

$SkillName = "liquidglass"
$RepoOwner = "RmaNMetaverse"
$RepoName = "Apple-LiquidGlass-Skill"
$Branch = "main"
$RawBaseUrl = "https://raw.githubusercontent.com/$RepoOwner/$RepoName/$Branch"

$CurrentDir = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }

$SkillFiles = @(
    "SKILL.md",
    "references/config-options.md",
    "examples/react.tsx",
    "examples/vanilla.html"
)

$Targets = @(
    "$HOME\.agents\skills\$SkillName",
    "$HOME\.claude\skills\$SkillName",
    "$HOME\.codex\skills\$SkillName",
    "$HOME\.gemini\config\skills\$SkillName"
)

Write-Host "Installing $SkillName skill across all AI agents..." -ForegroundColor Cyan

# Check if local files exist
$IsLocal = (Test-Path (Join-Path $CurrentDir "SKILL.md"))

foreach ($target in $Targets) {
    foreach ($file in $SkillFiles) {
        $destPath = Join-Path $target $file
        $destDir = Split-Path $destPath -Parent
        
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        }
        
        if ($IsLocal) {
            $srcPath = Join-Path $CurrentDir $file
            $resolvedSrc = if (Test-Path $srcPath) { (Resolve-Path $srcPath).Path } else { $null }
            $resolvedDest = if (Test-Path $destPath) { (Resolve-Path $destPath).Path } else { $null }

            if ($resolvedSrc -and ($resolvedSrc -ne $resolvedDest)) {
                Copy-Item -Path $srcPath -Destination $destPath -Force
            }
        } else {
            $url = "$RawBaseUrl/$file"
            Invoke-RestMethod -Uri $url -OutFile $destPath
        }
    }
    Write-Host "  [OK] Installed to $target" -ForegroundColor Green
}

Write-Host "Done! LiquidGlass skill is now available in GitHub Copilot, Claude Code, ChatGPT/Codex, Antigravity, and .agents." -ForegroundColor Yellow
