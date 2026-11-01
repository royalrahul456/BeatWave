# BeatWave — Confirmed Product Decisions

These decisions are confirmed for the initial project brief.

| Area | Confirmed decision |
|---|---|
| Product name | BeatWave |
| Visual theme | Black + Cyan |
| Client platform | Telegram Mini App only |
| Group playback model | Synchronized listening room |
| Room tenancy | One independent room per Telegram group |
| Audio model | Each member's client streams independently |
| Song requests | Everyone can request tracks |
| Playback control | DJ controls playback |
| Bot role | Group commands, room creation, notifications, Mini App launch |
| Mini App role | Search, room, player, queue, members, synchronized audio client |

## Not yet decided
- Which authorized music catalogue/audio provider will be used.
- Whether group admins automatically become DJs.
- Whether a temporary DJ is allowed when no DJ is assigned.
- Request duplicate policy and exact per-user rate limits.
- Whether song history is enabled by default.
- Hosting provider, domain, and production sizing.

## Recommended defaults
- Verified group admins can appoint a DJ.
- If no DJ is assigned, verified group admins can control playback; do not silently promote arbitrary members.
- Everyone may add requests subject to rate limits.
- Duplicate track requests are allowed only if the group setting enables them; otherwise detect duplicates in the upcoming queue.
- Enable short room history for usability, with a documented retention period.
- Start with a clearly labelled demo audio provider until an authorized production provider is selected.
