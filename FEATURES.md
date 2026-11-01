# BeatWave — Product Features

## 1. Core experience
- A Telegram group has one independent BeatWave music room.
- `/play <query>` starts a search/request flow.
- The first request creates the room if necessary.
- The bot posts a Mini App launch button in the group.
- All group members can open the room and listen on their own devices.
- Members joining mid-song start at the current server-calculated position.
- Different groups never share queue or playback state.

## 2. Member features
- Search the authorized music catalogue.
- Add a track to the shared queue.
- View the current track and upcoming queue.
- View the current DJ and listener count.
- View track artwork, title, artist, duration, and source attribution.
- See playback state updates in real time.
- Reconnect and resynchronize after network loss.
- Receive clear feedback when autoplay needs a user gesture or a track is unavailable.

## 3. DJ features
- Play, pause, resume, skip, and seek.
- Shuffle queue.
- Set repeat mode: off, current track, or queue.
- Remove queue items and clear queue.
- Appoint or hand over DJ role where group policy permits.
- Close the room or stop playback, with explicit confirmation for destructive actions.

## 4. Group admin features
- Configure room settings.
- Appoint/remove DJ.
- Close or reopen a room.
- Set request limits and duplicate-track policy.
- Configure who may moderate the queue.
- View recent room activity if history is enabled.

## 5. Platform admin features
- Configure provider adapters and credentials.
- Enable/disable providers.
- Monitor health, errors, stream expiry, and rate limits.
- Manage abuse reports and takedown requests.
- Inspect audit events for privileged actions.

## 6. Initial command set
See `BOT_COMMANDS.md`. Minimum commands: `/start`, `/help`, `/play`, `/queue`, `/room`, `/pause`, `/resume`, `/skip`, `/stop`, `/shuffle`, `/loop`, `/remove`, `/clear`, `/dj`, `/settings`.

## 7. Initial non-goals
- Telegram voice chat streaming.
- Standalone website or PWA.
- Native Android/iOS apps.
- Offline music downloads.
- User-to-user audio uploads unless moderation, storage, and rights handling are designed.
- Lyrics unless a licensed lyrics provider is integrated.
- Premium subscriptions and payments until core functionality is stable.

## 8. Reliability requirements
- Room state survives API/bot restarts.
- Queue mutations are transactional.
- Bot update processing is idempotent.
- WebSocket clients can reconnect and request a fresh snapshot.
- Provider errors do not corrupt room state.
- Multiple groups operate independently.
- A failed or expired audio source can be refreshed or marked unavailable.
