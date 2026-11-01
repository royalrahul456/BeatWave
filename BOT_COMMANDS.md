# BeatWave — Telegram Bot Commands

## 1. General commands

| Command | Who can use | Behavior |
|---|---|---|
| `/start` | Anyone | Explain BeatWave and launch Mini App where applicable |
| `/help` | Anyone | Show command list and role rules |
| `/play <query>` | Group members | Search and add a track request to the group room |
| `/queue` | Group members | Show current and upcoming tracks |
| `/room` | Group members | Post/retrieve the Mini App room button |
| `/dj` | Group members | Show current DJ and role information |
| `/history` | Group members | Show recent tracks if history is enabled |

## 2. DJ-only playback commands

| Command | Behavior |
|---|---|
| `/pause` | Pause current track |
| `/resume` | Resume current track |
| `/skip` | Skip current track |
| `/stop` | Stop current playback; do not silently delete room |
| `/shuffle` | Shuffle upcoming queue |
| `/loop` | Cycle or select off / track / queue |
| `/remove <position>` | Remove a queue item |
| `/clear` | Clear upcoming queue after confirmation |

## 3. Group admin commands
- `/settings` — show settings and admin actions.
- `/setdj` — appoint DJ through a validated user selection or Mini App flow.
- `/closedj` — remove current DJ assignment if policy allows.
- `/closeroom` — close room after confirmation.

Command names may be adapted to Telegram's command naming constraints. Avoid ambiguous command aliases.

## 4. Permission policy
- Everyone can request songs.
- DJ controls playback.
- Verified Telegram group admins can appoint/remove DJ and configure room settings.
- If no DJ is assigned, behavior follows a configurable default. Recommended default: verified group admins can control playback; optionally allow the first requester to become temporary DJ only if group settings enable it.
- Never trust role information supplied by the Mini App client.
- Bot must verify group admin status through Telegram Bot API where needed.

## 5. `/play` flow
1. Validate command arguments.
2. Identify Telegram group and requesting user.
3. Check per-user request rate limit.
4. Search authorized catalogue.
5. If multiple results, return inline selection buttons.
6. On selection, add request transactionally.
7. Create/reuse the group's room.
8. Post concise confirmation and Mini App button.
9. If provider is not configured, explain that demo mode or a provider setup is required; do not pretend the track is playing.

## 6. Bot response guidelines
- Use concise, friendly messages.
- Include track title, artist, requester, and queue position when available.
- Show the Mini App button prominently.
- For DJ-only command attempts, explain who can control playback.
- For unavailable tracks, offer search again or another result.
- Never expose internal errors, credentials, or signed audio URLs.
