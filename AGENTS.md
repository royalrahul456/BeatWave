# AGENTS.md — BeatWave project instructions

## Project identity
BeatWave is a Telegram group music listening platform with a Telegram bot and Telegram Mini App. The selected theme is Black + Cyan. The selected permission model is: everyone can request tracks; DJ controls playback.

## Scope guardrails
- Build Telegram Mini App only. Do not add a standalone website, PWA, Android, iOS, or desktop app.
- Do not write or imply that the bot streams audio into Telegram voice chat. Playback is in each member's Mini App client.
- One independent music room per Telegram group.
- The server owns the authoritative playback state.
- Use only music/audio sources with explicit rights and API permissions for this product. Demo mode may use only authorized sample assets.
- Never scrape or rip music from consumer streaming/video services or bypass DRM/access controls.

## Glassmorphism reference
- Use `LIQUID_GLASS_REFERENCE.md` and the user's repository https://github.com/RmaNMetaverse/Apple-LiquidGlass-Skill as the selected liquid-glass reference.
- Activate/read its project skill at `.agents/skills/liquidglass/SKILL.md` before implementing the visual layer.
- Verify `@ybouane/liquidglass` API compatibility from the installed package.
- Use optical glass selectively with Black + Cyan styling; do not overuse blur/glow.
- Keep a CSS fallback and ensure core functionality works without WebGL.
- Clean up WebGL instances on component unmount and test Telegram WebView performance.

## Engineering rules
- Prefer a modular monolith over premature microservices.
- Keep secrets in environment variables; commit only `.env.example`.
- Validate Telegram Mini App `initData` on the backend. Never trust client-supplied identity or role claims.
- Enforce DJ/admin permissions on the server for every playback-control operation.
- Use migrations for schema changes.
- Add tests for new business logic, API routes, permissions, and synchronization behavior.
- No dead buttons, fake integrations, silent exception swallowing, or placeholder success responses.
- Keep code typed, documented, and formatted consistently.
- Use transactions for queue mutations and playback transitions.
- Make webhook handlers idempotent and protect them with Telegram's webhook secret token.
- Avoid storing unnecessary personal data or sensitive tokens in logs.

## UI rules
- Mobile-first Telegram WebView layout.
- Black/charcoal surfaces with cyan accents.
- Strong contrast, clear focus states, reduced-motion support.
- Include loading, empty, error, offline, reconnecting, and autoplay-blocked states.
- Do not copy another music app's exact visual design.

## Workflow
1. Inspect the repository before editing.
2. Read `MASTER_PROMPT.md`, `ARCHITECTURE.md`, `FEATURES.md`, and `UI_DESIGN.md`.
3. Keep `TASKS.md` current.
4. Work in small milestones and run tests after each.
5. Do not overwrite existing user files without checking.
6. Report blockers honestly, especially audio-provider rights/credentials.
