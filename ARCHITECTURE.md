# BeatWave — System Architecture

## 1. High-level architecture

```text
Telegram Group
   | Bot commands / inline buttons
   v
Telegram Bot (aiogram)
   | authenticated internal calls
   v
FastAPI Backend
   |----------------------|
   |          |           |
Room Service Queue     Auth/Role Service
   |          |           |
   |      PostgreSQL      |
   |          |           |
Playback State Service   |
   |                     |
Redis Pub/Sub + WebSocket Gateway
   |
Telegram Mini App clients (one per listener)
   |
Authorized audio provider / demo audio CDN
```

## 2. Components

### Telegram bot
- Receives group commands and callbacks.
- Identifies the Telegram chat and sender.
- Calls backend services to search/request tracks and retrieve room details.
- Posts queue updates and Mini App launch buttons.
- Does not own the canonical queue or playback state.

### FastAPI backend
- Validates Telegram Mini App authentication.
- Exposes REST APIs.
- Enforces access, role, and rate-limit rules.
- Owns room, queue, and playback state transitions.
- Integrates catalogue and audio delivery adapters.
- Publishes events to Redis for WebSocket fan-out.

### PostgreSQL
- Persistent source of truth for users, groups, rooms, queue, roles, and playback snapshots.
- Uses transactions and constraints for concurrent queue changes.

### Redis
- Pub/sub for real-time event distribution.
- Short-lived presence and rate-limit data.
- Do not use Redis as the only persistent queue or playback store.

### WebSocket gateway
- Authenticates connection.
- Authorizes room membership.
- Sends initial snapshot and versioned events.
- Handles heartbeat, reconnect, and stale event protection.

### Telegram Mini App
- React + TypeScript client.
- Uses Telegram Web App SDK.
- Requests a server session using raw Telegram `initData`.
- Renders room UI and controls.
- Streams authorized audio independently on each member's device.

### Provider adapters
Separate catalogue search from audio delivery. A provider may support search but not playback in a third-party app; do not assume one implies the other.

## 3. Room lifecycle
- `created`: room record exists, no active track.
- `playing`: active track is playing.
- `paused`: active track is paused.
- `idle`: no current track.
- `ended`: room explicitly closed.
- `unavailable`: room temporarily cannot be served.

Default: one active room per Telegram group. Reopening should reuse the active room or create a new room according to documented group settings.

## 4. Playback synchronization model

Persist:
- `status`
- `current_track_id`
- `position_ms`
- `started_at` (UTC server timestamp when playback began/resumed)
- `paused_at`
- `playback_rate`
- `loop_mode`
- `version`

For a playing track:

`current_position_ms = position_at_start_ms + (server_now - started_at) * playback_rate`

Clamp position to track duration. The backend returns a snapshot with server time. Clients estimate server offset and calculate position locally, then periodically reconcile.

### Event ordering
Every state-changing event increments a room playback version. Clients ignore events with versions less than or equal to the last applied version. On gaps or reconnect, fetch a full snapshot.

### Drift handling
- Small drift: gently adjust playback rate within a safe narrow range if supported.
- Large drift: seek to authoritative position.
- Avoid aggressive seeking that causes audible glitches.
- Document that network and device differences prevent perfect sample-accurate synchronization.

## 5. Concurrency
- Use database transactions for queue append, remove, shuffle, and track advance.
- Use row-level locking or optimistic version checks for playback transitions.
- Make bot updates and repeated client actions idempotent.
- Ensure two simultaneous `/play` requests do not create duplicate active rooms.
- Use unique constraints for active room per group and provider-scoped track identifiers where appropriate.

## 6. Security boundaries
- Telegram initData is validated server-side.
- Frontend-supplied chat ID, user ID, role, or admin status is untrusted until verified.
- WebSocket connections require authenticated session and room authorization.
- Bot-to-backend requests use a private service credential or signed internal request.
- Provider secrets and bot token are server-only.
- Use HTTPS, secure headers, rate limits, CORS allowlists, and structured audit logging.

## 7. Deployment topology
For initial production, use Docker Compose on a Linux VPS:
- `bot`
- `api`
- `frontend` static build served through reverse proxy
- `postgres`
- `redis`
- `caddy` or `nginx`

Use managed PostgreSQL/Redis or separate persistent volumes and backups for production. Never expose database or Redis ports publicly.
