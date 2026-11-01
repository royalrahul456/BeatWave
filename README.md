# BeatWave — Project Documentation Kit

BeatWave is a Telegram group music platform. A group member requests a song using a bot command; the bot creates or reuses a room for that group; members open the Telegram Mini App and listen to synchronized playback on their own devices.

## Selected product decisions

| Item | Decision |
|---|---|
| Product name | BeatWave |
| Theme | Black + Cyan |
| Client | Telegram Mini App only |
| Group model | One independent room per Telegram group |
| Playback | Synchronized client-side streaming |
| Requests | All room members can request tracks |
| Playback controls | DJ controls playback |
| Bot | Python + aiogram |
| API | Python + FastAPI |
| Frontend | React + TypeScript |
| Database | PostgreSQL |
| Real-time | Redis + WebSockets |
| Deployment | Dockerized Linux VPS |

## Important playback distinction

BeatWave does not create a Telegram voice chat or broadcast one audio stream through Telegram. Each member's Mini App streams audio independently from an authorized source. The backend synchronizes track identity, playback position, and control state.

## Glassmorphism reference

The UI must use the selected [Apple-LiquidGlass-Skill repository](https://github.com/RmaNMetaverse/Apple-LiquidGlass-Skill) as the implementation reference for selective liquid-glass surfaces. See `LIQUID_GLASS_REFERENCE.md` for Antigravity skill setup, package integration guidance, Telegram WebView constraints, and acceptance checks.

## Documentation index

- `MASTER_PROMPT.md` — full Antigravity build instruction.
- `AGENTS.md` — persistent project guardrails for the coding agent.
- `FEATURES.md` — product behavior and feature requirements.
- `ARCHITECTURE.md` — system components and data flows.
- `DATABASE.md` — entities, relationships, and constraints.
- `API_SPEC.md` — REST and WebSocket contract.
- `UI_DESIGN.md` — design system and screen requirements.
- `LIQUID_GLASS_REFERENCE.md` — selected GitHub skill, Antigravity setup, library guidance, and WebView fallback.
- `BOT_COMMANDS.md` — Telegram commands and permission rules.
- `DEPLOYMENT.md` — local and VPS deployment guidance.
- `TASKS.md` — milestone checklist.
- `.env.example` — configuration variable template.

## How to use with Google Antigravity

1. Create an empty folder or open the repository you want Antigravity to work in.
2. Copy these documentation files into the repository root (or keep them in a `docs/` folder and update references accordingly).
3. Open the repository in Antigravity.
4. Ask Antigravity to read `AGENTS.md` and `MASTER_PROMPT.md` first.
5. Tell it to inspect the existing repository, create a milestone plan, and implement one milestone at a time.
6. Review provider terms and rights before enabling real music playback.

## Non-negotiable legal and technical note

A music search result or a Spotify/YouTube URL does not automatically grant BeatWave permission to stream that audio. Select a provider whose current terms expressly permit the intended playback in a third-party synchronized listening application. Until then, use a clearly labelled demo provider with public-domain/openly licensed or owner-supplied audio.

## Suggested first Antigravity instruction

> Read `AGENTS.md` and all project documentation. Inspect this repository without overwriting existing work. Return a concise architecture summary, identify any unresolved provider/legal decisions, create or update `TASKS.md`, and implement only Milestone 1 (repository scaffold and configuration). Do not claim audio playback works until an authorized provider or demo audio source is configured and tested.
