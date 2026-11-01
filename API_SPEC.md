# BeatWave — API and WebSocket Specification

Base path: `/api/v1`

All JSON responses should use consistent error shapes. Include request/correlation IDs. Validate all inputs with Pydantic.

## 1. Authentication

### `POST /telegram/session`
Purpose: validate Telegram Mini App `initData` and establish an application session.

Request:
```json
{ "init_data": "<raw Telegram WebApp initData string>" }
```

Rules:
- Validate Telegram's documented HMAC signature server-side with the bot token.
- Validate `auth_date` freshness.
- Never authenticate from `initDataUnsafe`.
- Return only the minimum user/session data needed by the client.
- Do not log raw initData.

## 2. Health

### `GET /health`
Return API health and dependency status suitable for monitoring. Do not expose secrets or internal diagnostics publicly.

## 3. User

### `GET /me`
Return authenticated Telegram user profile fields needed by the Mini App.

## 4. Room

### `GET /rooms/{room_id}`
Return room metadata, current user's permissions, current DJ, and room status. Verify the authenticated user may access this room.

### `GET /rooms/{room_id}/state`
Return authoritative playback snapshot, server timestamp, current track metadata, and playback version.

### `GET /rooms/{room_id}/queue`
Return current track and upcoming queue, with pagination if needed.

### `GET /rooms/{room_id}/members`
Return room presence summary and DJ identity. Minimize exposed user data.

## 5. Requests and queue

### `POST /rooms/{room_id}/search`
Request:
```json
{ "query": "track or artist" }
```
Return catalogue results with provider attribution and availability.

### `POST /rooms/{room_id}/requests`
Request:
```json
{ "provider": "configured-provider", "provider_track_id": "provider-id", "idempotency_key": "uuid" }
```
Allow authenticated room members to request tracks. Enforce provider validity, rate limits, and duplicate policy. Return queue item and updated queue version.

### `DELETE /rooms/{room_id}/queue/{item_id}`
DJ or authorized moderator only.

## 6. DJ controls

- `POST /rooms/{room_id}/controls/pause`
- `POST /rooms/{room_id}/controls/resume`
- `POST /rooms/{room_id}/controls/skip`
- `POST /rooms/{room_id}/controls/seek` body `{ "position_ms": 12345 }`
- `POST /rooms/{room_id}/controls/shuffle`
- `POST /rooms/{room_id}/controls/loop` body `{ "mode": "off|track|queue" }`
- `POST /rooms/{room_id}/controls/stop`

All control routes must enforce DJ/admin policy on the server and increment the playback version on successful state changes. Use idempotency/version checks where appropriate.

## 7. Group/admin operations
- `POST /rooms/{room_id}/dj` — appoint or hand over DJ, restricted to verified group admins or current DJ according to policy.
- `DELETE /rooms/{room_id}/dj/{user_id}` — remove DJ role, restricted.
- `PATCH /groups/{group_id}/settings` — verified group admin only.
- `POST /rooms/{room_id}/close` — verified group admin or authorized DJ policy.

## 8. WebSocket

Endpoint example: `/api/v1/rooms/{room_id}/ws`

Connection requirements:
- Authenticated application session.
- Room access authorization.
- Origin validation.
- Heartbeat and idle timeout.
- Reconnect with fresh snapshot.
- Backpressure handling and safe disconnect.

Event envelope:
```json
{
  "type": "playback.paused",
  "room_id": "uuid",
  "version": 18,
  "server_time": "2026-01-01T12:00:00Z",
  "payload": {}
}
```

Events:
- `room.snapshot`
- `playback.started`
- `playback.paused`
- `playback.resumed`
- `playback.seeked`
- `playback.track_changed`
- `playback.stopped`
- `queue.updated`
- `room.member_joined`
- `room.member_left`
- `room.dj_changed`
- `room.closed`
- `server.ping`
- `server.pong`

Clients must:
- Ignore stale versions.
- Request snapshot after a version gap.
- Reconnect with exponential backoff and jitter.
- Avoid treating a client-side action as successful until server confirmation arrives.

## 9. Error codes
Use stable application codes such as:
- `AUTH_INVALID`
- `AUTH_EXPIRED`
- `ROOM_NOT_FOUND`
- `ROOM_ACCESS_DENIED`
- `DJ_PERMISSION_REQUIRED`
- `TRACK_UNAVAILABLE`
- `PROVIDER_NOT_CONFIGURED`
- `REQUEST_RATE_LIMITED`
- `QUEUE_ITEM_NOT_FOUND`
- `PLAYBACK_CONFLICT`
- `VALIDATION_ERROR`
- `SERVICE_UNAVAILABLE`

Never return stack traces or provider secrets to clients.
