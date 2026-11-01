# BeatWave — Deployment Guide

This document is a deployment plan, not a claim that the project has already been implemented.

## 1. Prerequisites
- Linux VPS with a supported distribution.
- Domain name and DNS access.
- HTTPS certificate via Caddy or Nginx + ACME.
- Telegram bot created through BotFather.
- PostgreSQL database.
- Redis instance.
- Authorized music catalogue/audio delivery provider and required credentials/rights, or clearly labelled demo audio assets.
- Docker Engine and Docker Compose plugin.

## 2. Environment configuration
Copy `.env.example` to `.env` on the server and fill values securely. Never commit `.env`.

Required categories:
- Environment and public API URL.
- Telegram bot token and webhook secret.
- PostgreSQL connection string.
- Redis connection URL.
- Session signing/encryption secret.
- CORS allowed origins.
- Provider credentials.
- Logging level and rate-limit settings.

Use a secret manager or protected deployment environment where possible. Restrict file permissions.

## 3. Telegram setup
1. Create the bot with BotFather.
2. Configure bot name, description, commands, and Mini App entry point.
3. Set the Mini App URL to the HTTPS frontend domain.
4. Configure webhook URL and webhook secret token, or use polling only for local development.
5. Add bot to a test group with only required permissions.
6. Verify group command behavior and admin checks.

## 4. Docker services
Expected production services:
- `api`
- `bot`
- `frontend` (static build)
- `postgres`
- `redis`
- `proxy`

Do not expose PostgreSQL or Redis to the public internet. Persist PostgreSQL data. Configure health checks and restart policies.

## 5. Database
- Run Alembic migrations as a controlled deployment step.
- Back up before schema changes.
- Verify migration success before routing traffic.
- Test restore procedures periodically.

## 6. HTTPS and networking
- Serve the Mini App and API over HTTPS.
- Configure reverse proxy routes for API and WebSocket upgrade.
- Set strict CORS allowlist.
- Set secure headers.
- Use firewall rules to expose only required ports (typically 80/443 and restricted SSH).

## 7. Monitoring
- Health endpoint.
- Structured application logs with request IDs.
- Error monitoring.
- CPU, memory, disk, DB connection, and Redis monitoring.
- WebSocket connection counts.
- Provider error/latency and stream expiry metrics.
- Queue processing and bot webhook failure alerts.

Never log bot tokens, initData, session secrets, or signed playback URLs.

## 8. Production readiness checklist
- [ ] Telegram initData validation verified.
- [ ] Webhook secret validation verified.
- [ ] DJ/admin permissions enforced server-side.
- [ ] HTTPS and WebSocket TLS working.
- [ ] Provider rights and terms reviewed for synchronized third-party playback.
- [ ] Audio source expiry and refresh tested.
- [ ] Multiple groups tested independently.
- [ ] Two or more clients tested in one room.
- [ ] Join-mid-track and reconnect tested.
- [ ] Rate limits and abuse controls enabled.
- [ ] Backups and restore tested.
- [ ] Logs and monitoring configured.
- [ ] Privacy and retention policy reviewed.
