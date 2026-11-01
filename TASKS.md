# BeatWave — Development Checklist

Antigravity should update this file as work progresses. Do not mark a task complete unless it has been implemented and verified.

## Milestone 0 — Repository inspection and plan
- [x] Inspect existing repository and avoid overwriting user work.
- [x] Read all BeatWave documentation.
- [x] Confirm unresolved music-provider/legal requirements.
- [x] Produce implementation plan and repository map.

## Milestone 1 — Scaffold and configuration
- [x] Create bot/backend/frontend/infra/tests/docs structure.
- [x] Add typed configuration and `.env.example`.
- [x] Add Docker Compose for local services.
- [x] Add linting, formatting, and test configuration.
- [x] Add health endpoint.
- [x] Document local startup.

## Milestone 2 — Database and domain
- [x] Implement SQLAlchemy models.
- [x] Add Alembic initial migration.
- [x] Implement room lifecycle.
- [x] Implement queue service with transactions.
- [x] Implement playback state service and versioning.
- [x] Add domain/service tests.

## Milestone 3 — Telegram bot
- [x] Configure aiogram.
- [x] Implement `/start` and `/help`.
- [x] Implement group `/play` search/request flow.
- [x] Implement `/queue` and `/room`.
- [x] Implement DJ-only commands.
- [x] Add inline keyboards and Mini App launch button.
- [x] Add idempotent webhook handling and rate limits.
- [x] Test group isolation.

## Milestone 4 — Mini App authentication and UI shell
- [x] Integrate Telegram Web App SDK.
- [x] Validate initData server-side.
- [x] Implement authenticated session.
- [x] Build Black + Cyan design system.
- [x] Build room, search, queue, members, and error states.
- [x] Test Telegram WebView viewport behavior.

## Milestone 5 — Demo catalogue and audio
- [x] Implement provider interfaces.
- [x] Add clearly labelled demo provider.
- [x] Use only authorized sample audio.
- [x] Implement audio player and autoplay-blocked state.
- [x] Handle errors, expiry, and unavailable tracks.
- [x] Add tests.

## Milestone 6 — Real-time synchronization
- [x] Implement WebSocket authentication/authorization.
- [x] Implement versioned room events.
- [x] Implement authoritative server playback clock.
- [x] Implement join-mid-track snapshot.
- [x] Implement reconnect and resync.
- [x] Test drift handling across multiple clients.

## Milestone 7 — Roles and moderation
- [ ] Implement member request permissions.
- [ ] Implement DJ playback permissions.
- [ ] Verify Telegram group admins server-side.
- [ ] Implement DJ appointment and handover.
- [ ] Implement queue moderation and audit events.
- [ ] Test forged role/user/chat payloads.

## Milestone 8 — Authorized provider integration
- [ ] Select provider with rights for this exact use.
- [ ] Review provider API terms and territories.
- [ ] Add credentials securely.
- [ ] Implement catalogue search and playback-source adapter.
- [ ] Implement stream expiry/refresh.
- [ ] Verify attribution and provider restrictions.
- [ ] Do not enable if rights are unclear.

## Milestone 9 — QA and deployment
- [ ] Unit, integration, security, and E2E tests.
- [ ] Multiple-group concurrency test.
- [ ] Mobile Telegram WebView test.
- [ ] HTTPS and WebSocket production configuration.
- [ ] Backups, monitoring, and alerting.
- [ ] Deployment and rollback documentation.
- [ ] Production readiness review.
