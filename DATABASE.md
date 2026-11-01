# BeatWave — Database Design

Use PostgreSQL with SQLAlchemy 2.x and Alembic migrations. UUIDs are recommended for internal primary keys. Store Telegram numeric IDs as BIGINT. All timestamps should be timezone-aware UTC.

## 1. Tables

### users
- `id` UUID PK
- `telegram_user_id` BIGINT UNIQUE NOT NULL
- `username` nullable
- `display_name` nullable
- `created_at`, `updated_at`

Store only profile fields needed for the app.

### telegram_groups
- `id` UUID PK
- `telegram_chat_id` BIGINT UNIQUE NOT NULL
- `title` nullable
- `chat_type`
- `created_at`, `updated_at`

### music_rooms
- `id` UUID PK
- `group_id` UUID FK UNIQUE for one active room per group (adapt with partial unique index if room history is retained)
- `status`
- `current_track_id` nullable FK
- `created_by_user_id` nullable FK
- `created_at`, `updated_at`, `closed_at` nullable

### room_members
- `id` UUID PK
- `room_id` UUID FK
- `user_id` UUID FK
- `last_seen_at`
- `joined_at`
- `left_at` nullable
- Unique `(room_id, user_id)` for current membership or a history-friendly design with separate presence records.

### tracks
- `id` UUID PK
- `provider` NOT NULL
- `provider_track_id` NOT NULL
- `title`, `artist`, `album` nullable
- `duration_ms` nullable
- `artwork_url` nullable
- `source_attribution` nullable
- `availability_status`
- `created_at`, `updated_at`
- Unique `(provider, provider_track_id)`

Do not store long-lived signed audio URLs unless the provider's terms expressly allow it.

### queue_items
- `id` UUID PK
- `room_id` UUID FK
- `track_id` UUID FK
- `requested_by_user_id` UUID FK
- `position` integer
- `status` (queued/current/played/skipped/removed)
- `created_at`
- Index `(room_id, status, position)`

Use transactions to maintain queue ordering.

### playback_states
- `room_id` UUID PK/FK
- `current_queue_item_id` UUID FK nullable
- `status`
- `position_ms`
- `started_at` nullable
- `paused_at` nullable
- `playback_rate`
- `loop_mode`
- `version` BIGINT NOT NULL DEFAULT 0
- `updated_at`

### room_roles
- `id` UUID PK
- `room_id` UUID FK
- `user_id` UUID FK
- `role` (dj, moderator)
- `assigned_by_user_id` UUID FK
- `created_at`
- Unique `(room_id, user_id, role)`

Group-admin authority must be verified from trusted Telegram Bot API data, not merely stored as a client claim.

### group_settings
- `group_id` UUID PK/FK
- `requests_enabled` boolean
- `max_requests_per_user_window` integer
- `duplicate_policy`
- `allow_member_queue_moderation` boolean default false
- `temporary_dj_policy`
- `history_enabled` boolean
- `updated_at`

### room_history
- `id` UUID PK
- `room_id` UUID FK
- `track_id` UUID FK
- `requested_by_user_id` nullable FK
- `played_at`
- `ended_at` nullable
- `end_reason`

### audit_events
- `id` UUID PK
- `room_id` nullable FK
- `actor_user_id` nullable FK
- `action`
- `metadata` JSONB
- `created_at`

Do not put secrets or signed playback URLs in audit metadata.

## 2. Relationships
- One Telegram group has one active music room by default.
- A room has many members, queue items, roles, and history records.
- A queue item references one track and one requester.
- A playback state references the room and current queue item.
- A track is provider-scoped.

## 3. Constraints and indexes
- Unique Telegram user ID.
- Unique Telegram chat ID.
- Unique provider + provider track ID.
- Enforce one active room per group with a partial unique index if retaining closed room records.
- Index room queue by status and position.
- Index recent room history by room and played time.
- Add foreign keys and appropriate ON DELETE behavior.
- Avoid cascading deletion of audit/history data without a retention policy.

## 4. Migration requirements
- All schema changes through Alembic.
- Include an initial migration.
- Test migrations on an empty database.
- Document backup and rollback considerations.
