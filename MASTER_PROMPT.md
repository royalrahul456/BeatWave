# BeatWave — Master Build Prompt for Google Antigravity

You are the lead product engineer, software architect, UI/UX designer, security engineer, and QA engineer for **BeatWave**, a Telegram-first group music listening platform.

## 1. Product vision

Build a production-minded Telegram Music Bot + Telegram Mini App. A user types `/play <song name>` in a Telegram group. The bot finds an authorized audio source, creates or reuses one music room dedicated to that Telegram group, adds the requested track to that room's shared queue, and posts a **Join BeatWave** Mini App button. Group members open the Mini App and listen to the same track in synchronized playback on their own devices.

**Important product scope:** Telegram Mini App only. Do not build a standalone website, PWA, native Android app, iOS app, or desktop app unless explicitly requested later. The Mini App is the listening client. The Telegram bot is the group command and notification interface.

## 2. Brand and visual direction

- Product name: **BeatWave**
- Theme: **Black + Cyan**
- Visual style: premium, modern, minimal, music-focused, polished, responsive.
- Use near-black backgrounds, layered charcoal surfaces, cyan highlights, subtle glow only for active states, strong readable typography, crisp album artwork, and restrained motion.
- Avoid copying Spotify, Apple Music, YouTube Music, or any other product's exact layout or branding.
- Design mobile-first for Telegram's in-app browser. Support narrow phones, tablets, and desktop Telegram clients gracefully.
- Provide loading, empty, error, offline, reconnecting, and permission-denied states.
- Ensure accessible contrast, keyboard navigation where practical, semantic controls, and reduced-motion support.

## 2A. Liquid glass / glassmorphism reference — required

Use the user's selected GitHub skill repository as the glassmorphism implementation reference:
https://github.com/RmaNMetaverse/Apple-LiquidGlass-Skill

Before UI implementation:
- Read `LIQUID_GLASS_REFERENCE.md`.
- Install/activate the repository's `liquidglass` skill for this project at `.agents/skills/liquidglass/` using its documented Antigravity setup.
- Read the actual `SKILL.md`, README, examples, and relevant references from the repository.
- Verify the current `@ybouane/liquidglass` package API and version before integrating it.

Use `@ybouane/liquidglass` for selected premium glass surfaces in BeatWave, with Black + Cyan styling. Follow its structural requirements, lifecycle cleanup, and configuration guidance. Do not apply WebGL glass to every element. Provide a CSS glassmorphism fallback for WebViews/devices where WebGL is unavailable or too expensive. Test in Telegram's mobile WebView and preserve touch controls, accessibility, reduced-motion behavior, and performance.

Do not blindly run remote installer scripts; inspect them first. Prefer project-level skill installation so the project is reproducible. Do not copy the reference project's branding or exact demo UI.

## 3. Core user experience

### Group flow
1. A member sends `/play <query>` in a Telegram group.
2. The bot validates the command, identifies the Telegram group, and checks group configuration.
3. The backend searches the configured, legally authorized music catalogue.
4. The requester selects a result if multiple results are returned, or the best unambiguous result is added automatically according to product settings.
5. The backend creates a music room for that group if one does not already exist.
6. The track is added to that room's shared queue.
7. The bot posts a message with track information and a Telegram Mini App deep link / web_app button labelled **Open BeatWave** or **Join Music Room**.
8. Each member opens the Mini App and receives the current room state.
9. Each member's device streams the audio independently from the authorized source while following the room's server-authoritative playback timeline.

### Room behavior
- One active room per Telegram group by default.
- Different groups have independent queues and playback states.
- Reopening the room must restore the current state.
- A room can be idle, playing, paused, ended, or unavailable.
- Room membership is based on authenticated Telegram Mini App identity and room access rules.
- A user should not be able to join or control a room by guessing a room ID.
- If a user arrives mid-track, the client starts at the current server-calculated playback position.
- If a client reconnects, it fetches authoritative state and resynchronizes.

### Roles and permissions
- **Requester / Member:** may search and request tracks, view queue, view room members, and vote only if a future voting feature is enabled.
- **DJ:** controls playback (play, pause, resume, skip, seek, repeat, shuffle, and queue moderation as configured).
- **Group Admin:** can appoint/remove DJ, configure room settings, and close the room. Group-admin status must be verified using Telegram Bot API data or another trusted server-side method, never accepted from client-supplied fields.
- **Platform Admin:** manages catalogue integrations, moderation, service health, and global configuration.
- Initial policy: **Everyone can request; DJ controls playback.** If no DJ is assigned, use a configurable default policy: group admins can control playback, and the room creator/requester may be temporary DJ only if explicitly enabled. Make this behavior configurable and document the default.

## 4. Functional requirements

### Telegram bot
Implement commands and clear help:
- `/start` — explain the bot and how to add it to a group.
- `/help` — show available commands.
- `/play <query>` — search and request a track.
- `/queue` — show the shared room queue.
- `/room` — post or retrieve the room Mini App link.
- `/pause` — DJ-only pause.
- `/resume` — DJ-only resume.
- `/skip` — DJ-only skip.
- `/stop` — DJ-only stop/close playback, with clear distinction from closing the room.
- `/shuffle` — DJ-only queue shuffle.
- `/loop` — DJ-only loop mode (off / track / queue).
- `/remove <queue-position>` — DJ-only queue removal.
- `/clear` — DJ-only clear queue, with confirmation.
- `/dj` — show current DJ and available DJ management actions.
- `/settings` — group settings for admins.
- `/lyrics` — only if a licensed/authorized lyrics provider is integrated; otherwise explain unavailable.
- `/history` — show recent room tracks if enabled.

Use inline keyboards for search-result selection, confirmation, and opening the Mini App. Commands must respond with useful validation messages, not raw stack traces. Apply Telegram rate limits and command cooldowns.

### Mini App
Required screens/components:
- Room home / Now Playing
- Search
- Search results
- Shared queue
- Room members / DJ identity
- Track details
- Playback controls
- Room unavailable / ended
- Loading and reconnecting states
- Help / permissions explanation

Now Playing should show:
- Album art or a tasteful fallback
- Track title and artist
- Progress bar and elapsed / total time
- Play/pause state (read-only for members without DJ permission)
- Next track preview
- Queue count
- Current DJ
- Listener count
- Add-to-queue action

Search:
- Search only the configured authorized catalogue.
- Show title, artist, duration, artwork, source attribution, and availability.
- Handle no results, provider errors, and unavailable tracks.
- Never expose private provider credentials or raw signed URLs to logs or clients.

Queue:
- Display current track and upcoming tracks.
- Allow all members to add tracks.
- Only DJ can reorder/remove queue items unless group configuration explicitly grants moderation rights.
- Prevent duplicate spam with configurable duplicate policy and per-user request limits.

### Audio player and synchronization
- Use browser-native audio playback or a suitable streaming playback library compatible with Telegram WebView.
- The server is the source of truth for playback state.
- Store `status`, `track_id`, `position_ms`, `started_at`, `paused_at`, `playback_rate`, `loop_mode`, and monotonically increasing `version`.
- When playing, derive current position from server time and `started_at`; do not rely on a client timer as the source of truth.
- Broadcast versioned state events over WebSockets.
- On join/reconnect, fetch a fresh authoritative snapshot.
- Ignore stale or out-of-order events by version.
- Correct small drift gradually where possible; perform a seek/resync when drift exceeds a configured threshold.
- Handle autoplay restrictions: show a clear **Tap to listen** action when browser policy requires a user gesture.
- Handle audio errors, expired stream URLs, track unavailability, network loss, and app backgrounding.
- Do not promise perfect sample-accurate synchronization across different devices/networks. Target practical synchronized listening and explain limitations.
- Never attempt to bypass browser, Telegram, DRM, paywall, or provider restrictions.

## 5. Legal audio-source requirement — critical

Do **not** scrape, rip, download, proxy, or extract audio from YouTube, Spotify, Apple Music, or other services unless the provider explicitly grants the required rights and technical permissions for this use.

Implement a provider abstraction such as:
- `MusicCatalogProvider.search(query)`
- `MusicCatalogProvider.getTrack(track_id)`
- `AudioDeliveryProvider.getPlaybackSource(track_id, user_context)`
- `AudioDeliveryProvider.refreshPlaybackSource(track_id, user_context)`

Use a documented, authorized source only. The first integration must be selected based on its current API terms, territories, licensing, playback rights, and whether it permits synchronized group listening in a third-party Mini App. If no suitable provider credentials/rights are configured, implement a **local demo provider** that plays only sample audio assets that are public-domain, openly licensed for this use, or supplied by the project owner with rights. Clearly label demo content. Do not fake a successful real-world music search or playback.

Provider credentials must remain server-side. Respect attribution, stream expiry, territory restrictions, usage limits, and takedown requests. Do not persist provider stream URLs longer than permitted.

## 6. Technical architecture

Preferred stack:
- Bot: Python + aiogram (current stable compatible release)
- API: Python + FastAPI
- Frontend: React + TypeScript + Vite
- Styling: Tailwind CSS (or another consistent utility/design system)
- Database: PostgreSQL
- Cache / pub-sub / ephemeral state: Redis
- Real-time: WebSockets
- Migrations: Alembic
- ORM: SQLAlchemy 2.x
- Validation: Pydantic
- Tests: pytest, frontend unit tests, browser/E2E tests
- Deployment: Docker Compose for local development; production-ready container images for VPS deployment
- Reverse proxy / TLS: Caddy or Nginx

Use a modular monolith initially. Do not introduce microservices without a measured need. Keep bot, API, domain services, provider adapters, and frontend logically separated.

## 7. Telegram Mini App security

- Validate Telegram `initData` on the backend using Telegram's documented HMAC validation process and bot token. Never trust `initDataUnsafe` as authentication.
- Enforce `auth_date` freshness and reject invalid signatures.
- Use a server-issued session after validation; use secure, HttpOnly cookies where compatible or short-lived scoped tokens with careful storage.
- Verify that the Telegram user is allowed to access the requested group room.
- Never accept `user_id`, `chat_id`, admin status, or DJ status as trusted solely because the frontend sent it.
- Validate Bot API webhook secret token when using webhooks.
- Use HTTPS everywhere outside local development.
- Apply request validation, rate limiting, CSRF protections where applicable, secure CORS, and WebSocket origin/auth checks.
- Avoid logging bot tokens, provider secrets, initData, signed playback URLs, or sensitive personal data.
- Include a `.env.example` with placeholders only. Never commit actual secrets.

## 8. Data model

Create normalized tables/entities for:
- `users`
- `telegram_groups`
- `group_memberships` (only if needed and with minimal stored data)
- `music_rooms`
- `room_members`
- `tracks` (provider-scoped identifiers)
- `queue_items`
- `playback_states`
- `room_roles` or role assignments
- `user_favorites` (optional for initial group-only scope; keep extensible)
- `room_history`
- `group_settings`
- `audit_events` for privileged actions

Use UUIDs for internal IDs, unique constraints for Telegram group IDs and one active room per group, foreign keys, indexes for common queries, created/updated timestamps, and safe deletion/retention rules. Do not store unnecessary Telegram profile data.

## 9. API and real-time contract

Design documented REST endpoints, for example:
- `GET /health`
- `GET /api/v1/me`
- `POST /api/v1/telegram/session`
- `GET /api/v1/rooms/{room_id}`
- `GET /api/v1/rooms/{room_id}/state`
- `GET /api/v1/rooms/{room_id}/queue`
- `POST /api/v1/rooms/{room_id}/requests`
- `POST /api/v1/rooms/{room_id}/controls/pause`
- `POST /api/v1/rooms/{room_id}/controls/resume`
- `POST /api/v1/rooms/{room_id}/controls/skip`
- `POST /api/v1/rooms/{room_id}/controls/seek`
- `POST /api/v1/rooms/{room_id}/controls/shuffle`
- `DELETE /api/v1/rooms/{room_id}/queue/{item_id}`

All control endpoints must enforce server-side DJ/admin authorization. Request endpoints must enforce rate limits and validation.

WebSocket events should be versioned and typed:
- `room.snapshot`
- `playback.started`
- `playback.paused`
- `playback.resumed`
- `playback.seeked`
- `playback.track_changed`
- `queue.updated`
- `room.member_joined`
- `room.member_left`
- `room.dj_changed`
- `room.closed`
- `server.ping` / `server.pong`

Document payload schemas and reconnection behavior.

## 10. Quality requirements

- No dead buttons or fake controls.
- No hardcoded secrets.
- No client-side authorization.
- No fabricated provider functionality.
- No direct database access from frontend.
- No unbounded in-memory queue as the only source of truth.
- Use database transactions for queue and playback mutations.
- Use idempotency or deduplication for repeated bot updates and control requests.
- Provide structured logs, request IDs, metrics, and health checks.
- Provide useful user-facing error messages.
- Test multiple groups simultaneously to prove isolation.
- Test two or more Mini App clients in the same room for synchronization.
- Test a member joining mid-track, reconnecting, and receiving the current position.
- Test permissions: member cannot pause/skip; DJ can; admin can appoint DJ.
- Test invalid Telegram initData and forged user/chat IDs.
- Test mobile Telegram WebView behavior and autoplay restrictions.

## 11. Required project outputs

Create a complete, organized repository with:
- `bot/`
- `backend/`
- `frontend/`
- `infra/`
- `docs/`
- `tests/`
- `README.md`
- `AGENTS.md`
- `.env.example`
- `docker-compose.yml`
- database migrations
- OpenAPI documentation
- setup and deployment guides
- test instructions
- provider integration notes
- a clearly labelled demo mode

Before coding, inspect the repository and report its current state. If empty, initialize it. Do not overwrite existing user work. Maintain a `TASKS.md` checklist and update it as work is completed.

## 12. Execution strategy

Work in milestones and keep the project runnable after each milestone:

1. Architecture and repository scaffold.
2. Database models, migrations, configuration, health endpoint.
3. Telegram bot setup, group commands, room creation.
4. Telegram Mini App authentication and room shell.
5. Demo catalogue and authorized sample-audio playback.
6. Queue and server-authoritative playback state.
7. WebSocket synchronization across multiple clients.
8. DJ permissions and group administration.
9. Production provider adapter only after rights and credentials are confirmed.
10. Tests, security review, Docker deployment, documentation.

At the end of each milestone:
- Run relevant tests and linters.
- Fix failures before proceeding.
- Update documentation and `TASKS.md`.
- Summarize files created, decisions, commands run, tests passed, and remaining blockers.

If a requirement is ambiguous, choose the safest maintainable default and document it. Ask the user only when a decision genuinely blocks progress, especially for the licensed audio provider, credentials, or rights.

**Start by producing a concise implementation plan and repository scaffold. Then implement milestone by milestone. Do not claim the product is production-ready until provider rights, deployment, security, and end-to-end tests are verified.**
