import logging
import urllib.parse
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.services.api_client import api_client
from bot.handlers.general import get_mini_app_keyboard
from bot.config import bot_settings

logger = logging.getLogger("BeatWavePlayback")
router = Router()


def clean_md(text: str) -> str:
    """Strips Markdown symbols that break Telegram entity parser."""
    if not text:
        return ""
    for ch in ("*", "_", "`", "[", "]"):
        text = text.replace(ch, "")
    return text.strip()


def make_app_button(chat: types.Chat, room_id: str, text: str = "🌊 Open Music Room") -> InlineKeyboardButton:
    """
    Creates an inline button launching the native Telegram Mini App.
    Uses web_app=WebAppInfo to open the player directly in Telegram without external redirects.
    """
    app_url = f"{bot_settings.MINI_APP_URL}?room_id={room_id}"
    return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=app_url))


def make_progress_bar(current_ms: int, total_ms: int, bar_length: int = 12) -> str:
    if total_ms <= 0:
        return "▬" * bar_length
    ratio = min(1.0, max(0.0, current_ms / total_ms))
    filled = int(ratio * bar_length)
    bar = ""
    for i in range(bar_length):
        if i == filled:
            bar += "🔘"
        else:
            bar += "▬"
    return bar


def format_duration(ms: int) -> str:
    secs = max(0, ms // 1000)
    mins, s = divmod(secs, 60)
    return f"{mins}:{s:02d}"


# --- /nowplaying & /np ---

@router.message(Command("nowplaying"))
@router.message(Command("np"))
async def cmd_nowplaying(message: types.Message):
    chat = message.chat
    user = message.from_user

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    if not room:
        await message.reply("❌ Unable to connect to music room.")
        return

    room_id = room["id"]
    state = await api_client.get_playback_state(room_id, user.id)

    if not state or not state.get("current_queue_item"):
        is_group = chat.type in ("group", "supergroup", "channel")
        await message.reply(
            "🔇 *Nothing is currently playing.*\n\n"
            "Use `/play <song>` or open the Mini App to start the stream!",
            reply_markup=get_mini_app_keyboard(room_id, is_group=is_group),
            parse_mode="Markdown"
        )
        return

    item = state["current_queue_item"]
    track = item.get("track", {})
    status = state.get("status", "playing")
    status_icon = "▶ Playing" if status == "playing" else "⏸ Paused"
    loop_mode = state.get("loop_mode", "off")

    pos_ms = state.get("position_ms", 0)
    dur_ms = track.get("duration_ms", 0)
    progress_bar = make_progress_bar(pos_ms, dur_ms)
    time_display = f"`{format_duration(pos_ms)}` {progress_bar} `{format_duration(dur_ms)}`"

    requested_by = item.get("requested_by", {})
    req_name = requested_by.get("display_name") or requested_by.get("username") or "Member"

    text = (
        f"🎧 *Now Playing on BeatWave:*\n\n"
        f"🎵 *{clean_md(track.get('title', 'Unknown Track'))}*\n"
        f"👤 *Artist:* {clean_md(track.get('artist', 'Artist'))}\n"
        f"🙋 *Requested by:* {clean_md(req_name)}\n\n"
        f"📊 *Status:* {status_icon} | *Repeat:* `{loop_mode.upper()}`\n"
        f"{time_display}\n\n"
        f"🔊 *Synchronized audio is playing in your Mini App client.*"
    )

    is_dj = room.get("is_dj", False)
    buttons = []

    # DJ Quick Controls
    if is_dj:
        toggle_action = "pause" if status == "playing" else "resume"
        toggle_label = "⏸ Pause" if status == "playing" else "▶ Resume"
        buttons.append([
            InlineKeyboardButton(text=toggle_label, callback_data=f"dj:{toggle_action}"),
            InlineKeyboardButton(text="⏭ Skip", callback_data="dj:skip")
        ])

    # Group-safe Mini App button
    buttons.append([make_app_button(chat, room_id)])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    try:
        await message.reply(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        await message.reply(text, reply_markup=kb)


# --- /play <query> ---

@router.message(Command("play"))
@router.message(Command("p"))
async def cmd_play(message: types.Message):
    try:
        chat = message.chat
        user = message.from_user

        args = message.text.split(maxsplit=1) if message.text else []
        query = ""
        if len(args) >= 2:
            query = args[1].strip()
        elif message.reply_to_message and message.reply_to_message.text:
            query = message.reply_to_message.text.strip()

        if not query:
            await message.reply(
                "ℹ️ *Usage:* `/play <song title, artist, or Spotify link>`\n"
                "• Example: `/play Starboy The Weeknd`\n"
                "• Example: `/play Blinding Lights`\n"
                "• Tip: You can also reply to any message with `/play`!",
                parse_mode="Markdown"
            )
            return

        await _search_and_display(message, chat, user, query)
    except Exception as e:
        logger.error(f"[Playback] Error in cmd_play: {e}", exc_info=True)
        try:
            await message.reply("❌ Error processing request. Please try again.")
        except Exception:
            pass


# Private DM auto-search when sending any plain text
@router.message(F.chat.type == "private", ~F.text.startswith("/"))
async def private_text_search(message: types.Message):
    if not message.text or len(message.text.strip()) < 2:
        return
    await _search_and_display(message, message.chat, message.from_user, message.text.strip())


async def _search_and_display(message: types.Message, chat: types.Chat, user: types.User, query: str):
    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    if not room:
        await message.reply("❌ Error connecting to room backend.")
        return

    room_id = room["id"]
    safe_q = clean_md(query)

    try:
        status_msg = await message.reply(f"🔍 Searching catalogue for *{safe_q}*...", parse_mode="Markdown")
    except Exception:
        status_msg = await message.reply(f"🔍 Searching catalogue for {safe_q}...")

    try:
        results = await api_client.search_tracks(room_id, user.id, query)
    except Exception as e:
        logger.error(f"Search API exception: {e}")
        results = []

    if not results:
        try:
            await status_msg.edit_text(f"❌ No tracks found for *{safe_q}*. Please try another search term.", parse_mode="Markdown")
        except Exception:
            await status_msg.edit_text(f"❌ No tracks found for {safe_q}.")
        return

    user_name = clean_md(user.full_name or user.username or "Listener")

    # Check if a track is already currently playing in this room
    current_pb = room.get("playback_state")
    is_actively_playing = (
        current_pb is not None
        and current_pb.get("status") == "playing"
        and current_pb.get("current_queue_item") is not None
    )

    # Multi-track Spotify playlist import
    if "spotify.com" in query and len(results) > 1:
        track = results[0]
        # If already playing, queue all tracks; if idle, start first track
        first_play_now = not is_actively_playing
        await api_client.add_track_request(room_id, user.id, track["provider"], track["provider_track_id"], play_now=first_play_now)
        # Queue upcoming tracks from playlist
        for sub_track in results[1:15]:
            await api_client.add_track_request(room_id, user.id, sub_track["provider"], sub_track["provider_track_id"], play_now=False)

        duration_ms = track.get("duration_ms", 240000)
        dur_str = format_duration(duration_ms)
        clean_track_title = clean_md(track.get("title", "Track"))
        clean_artist = clean_md(track.get("artist", "Artist"))

        header = "💚 *Spotify Playlist Queued!*\n\n" if is_actively_playing else "💚 *Spotify Playlist Streaming!*\n\n"
        caption = (
            f"{header}"
            f"🎵 *{'Queued' if is_actively_playing else 'Now Streaming'}:* {clean_track_title}\n"
            f"👤 *Artist:* {clean_artist}\n"
            f"📂 *Queue:* {len(results)} songs added from Spotify\n"
            f"🕛 *Duration:* {dur_str} min\n"
            f"🙍🏻 *Requested by:* {user_name}"
        )
    else:
        # Direct play or queue: if playing, add to upcoming queue; if idle, stream immediately
        track = results[0]
        play_now = not is_actively_playing
        await api_client.add_track_request(room_id, user.id, track["provider"], track["provider_track_id"], play_now=play_now)

        duration_ms = track.get("duration_ms", 240000)
        dur_str = format_duration(duration_ms)
        clean_track_title = clean_md(track.get("title", query))

        provider = track.get("provider", "music")
        pid = track.get("provider_track_id", "")
        if provider == "youtube":
            track_url = f"https://www.youtube.com/watch?v={pid}"
        else:
            track_url = f"https://www.google.com/search?q={urllib.parse.quote(clean_track_title + ' song')}"

        header_title = "📂 Added to Queue" if is_actively_playing else "🎵 Started streaming"
        caption = (
            f"{header_title}\n"
            f"🎶 Title: [{clean_track_title}]({track_url})\n"
            f"🕛 Duration: {dur_str} min\n"
            f"🙍🏻 Requested by: {user_name}"
        )

    members_count = room.get("members_count", 1)
    app_btn = make_app_button(chat, room_id)
    is_group = chat.type in ("group", "supergroup", "channel")
    bot_user = bot_settings.BOT_USERNAME or "BeatWave_app"

    if is_group:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [app_btn],
                [
                    InlineKeyboardButton(text="🎧 Open via Bot DM", url=f"https://t.me/{bot_user}?start={room_id}"),
                    InlineKeyboardButton(text="⏭ Skip", callback_data="ctrl:skip"),
                ],
                [
                    InlineKeyboardButton(text=f"👥 In Room: {members_count} Listeners", callback_data=f"room_members:{room_id}"),
                ]
            ]
        )
    else:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [app_btn],
                [
                    InlineKeyboardButton(text=f"👥 In Room: {members_count} Listeners", callback_data=f"room_members:{room_id}"),
                    InlineKeyboardButton(text="⏭ Skip", callback_data="ctrl:skip"),
                ]
            ]
        )

    artwork_url = track.get("artwork_url") or "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800"

    try:
        await status_msg.delete()
    except Exception:
        pass

    # Multi-tier resilient message send (photo -> markdown text -> plain text)
    try:
        await message.answer_photo(
            photo=artwork_url,
            caption=caption,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    except Exception as e1:
        logger.warning(f"Could not send photo: {e1}")
        try:
            await message.reply(caption, reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=False)
        except Exception as e2:
            logger.warning(f"Could not send markdown: {e2}")
            plain_caption = f"🎵 Started streaming: {clean_md(track.get('title', 'Track'))}\nRequested by: {user_name}"
            safe_kb = InlineKeyboardMarkup(inline_keyboard=[[
                make_app_button(chat, room_id, "🌊 Open Player")
            ]])
            await message.reply(plain_caption, reply_markup=safe_kb)


@router.callback_query(F.data.startswith("room_members:"))
async def cb_room_members_info(query: types.CallbackQuery):
    room_id = query.data.split(":")[1]
    room = await api_client.get_room(room_id, query.from_user.id)
    if room:
        members = room.get("members", [])
        if members:
            names = [f"• {clean_md(m.get('display_name') or m.get('username') or 'Member')}" for m in members]
            text = f"👥 *Active Room Listeners ({len(members)}):*\n\n" + "\n".join(names)
        else:
            text = f"👥 *Listeners in Room:* {room.get('members_count', 1)}"
    else:
        text = "👥 *Listeners:* Active"
    await query.answer(text, show_alert=True)


# --- Callback query: Add track to queue ---

@router.callback_query(F.data.startswith("req:"))
async def cb_add_request(callback: types.CallbackQuery):
    user = callback.from_user
    chat = callback.message.chat

    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer("Invalid track data.")
        return

    _, provider, provider_track_id = parts

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    if not room:
        await callback.answer("Room not found.", show_alert=True)
        return

    room_id = room["id"]
    success, msg, item = await api_client.add_track_request(room_id, user.id, provider, provider_track_id)
    if not success or not item:
        await callback.answer(msg, show_alert=True)
        return

    track = item.get("track", {})
    dur = format_duration(track.get("duration_ms", 0))
    is_group = chat.type in ("group", "supergroup", "channel")

    await callback.message.edit_text(
        f"✅ *Added to Room Queue!* 🎶\n\n"
        f"🎵 *{clean_md(track.get('title', 'Track'))}*\n"
        f"👤 *Artist:* {clean_md(track.get('artist', 'Artist'))} • `{dur}`\n"
        f"🙋 *Queued by:* {clean_md(user.full_name)}\n\n"
        f"Tap below to listen in sync with the room:",
        reply_markup=get_mini_app_keyboard(room_id, is_group=is_group),
        parse_mode="Markdown"
    )
    await callback.answer("Added to queue!")


# --- Callback query: DJ inline controls ---

@router.callback_query(F.data.startswith("dj:"))
async def cb_dj_control(callback: types.CallbackQuery):
    user = callback.from_user
    chat = callback.message.chat
    action = callback.data.split(":", 1)[1]

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    if not room:
        await callback.answer("Room error.", show_alert=True)
        return

    room_id = room["id"]
    success, msg = await api_client.control_playback(room_id, user.id, action)
    if success:
        await callback.answer(f"Success: {action.title()}!")
        # Refresh current message
        state = await api_client.get_playback_state(room_id, user.id)
        if state and state.get("current_queue_item"):
            item = state["current_queue_item"]
            track = item.get("track", {})
            status = state.get("status", "playing")
            status_icon = "▶ Playing" if status == "playing" else "⏸ Paused"
            pos_ms = state.get("position_ms", 0)
            dur_ms = track.get("duration_ms", 0)
            progress_bar = make_progress_bar(pos_ms, dur_ms)

            toggle_action = "pause" if status == "playing" else "resume"
            toggle_label = "⏸ Pause" if status == "playing" else "▶ Resume"

            app_btn = make_app_button(chat, room_id)

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text=toggle_label, callback_data=f"dj:{toggle_action}"),
                    InlineKeyboardButton(text="⏭ Skip", callback_data="dj:skip")
                ],
                [app_btn]
            ])

            await callback.message.edit_text(
                f"🎧 *Now Playing on BeatWave:*\n\n"
                f"🎵 *{clean_md(track.get('title', 'Track'))}*\n"
                f"👤 *Artist:* {clean_md(track.get('artist', 'Artist'))}\n\n"
                f"📊 *Status:* {status_icon}\n"
                f"`{format_duration(pos_ms)}` {progress_bar} `{format_duration(dur_ms)}`\n\n"
                f"🔊 *Audio streaming in Mini App client.*",
                reply_markup=kb,
                parse_mode="Markdown"
            )
    else:
        await callback.answer(f"Failed: {msg}", show_alert=True)


# --- /queue ---

@router.message(Command("queue"))
async def cmd_queue(message: types.Message):
    chat = message.chat
    user = message.from_user

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    if not room:
        await message.reply("❌ Could not connect to room.")
        return

    room_id = room["id"]
    queue = await api_client.get_queue(room_id, user.id)
    is_group = chat.type in ("group", "supergroup", "channel")

    if not queue:
        await message.reply(
            "📭 *The queue is empty!*\n\n"
            "Use `/play <song>` or open the Mini App to request tracks.",
            reply_markup=get_mini_app_keyboard(room_id, "🎵 Search & Add Songs", is_group=is_group),
            parse_mode="Markdown"
        )
        return

    lines = ["🎵 *BeatWave Room Queue:*\n"]
    for idx, item in enumerate(queue):
        track = item.get("track", {})
        status = item.get("status")
        dur = format_duration(track.get("duration_ms", 0))
        if status == "current":
            prefix = "▶ *Now Playing:*"
        else:
            prefix = f"`#{idx + 1}`"
        lines.append(f"{prefix} *{clean_md(track.get('title', 'Track'))}* — {clean_md(track.get('artist', 'Artist'))} `({dur})`")

    text = "\n".join(lines)
    await message.reply(text, reply_markup=get_mini_app_keyboard(room_id, is_group=is_group), parse_mode="Markdown")


# --- DJ Control Commands ---

@router.message(Command("pause"))
async def cmd_pause(message: types.Message):
    await _handle_dj_action(message, "pause", "⏸ Playback paused.")


@router.message(Command("resume"))
async def cmd_resume(message: types.Message):
    await _handle_dj_action(message, "resume", "▶ Playback resumed.")


@router.message(Command("skip"))
async def cmd_skip(message: types.Message):
    await _handle_dj_action(message, "skip", "⏭ Skipped to next track.")


@router.message(Command("stop"))
async def cmd_stop(message: types.Message):
    await _handle_dj_action(message, "stop", "⏹ Playback stopped.")


@router.message(Command("loop"))
async def cmd_loop(message: types.Message):
    chat = message.chat
    user = message.from_user

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    if not room:
        await message.reply("❌ Error connecting to room.")
        return

    room_id = room["id"]
    state = await api_client.get_playback_state(room_id, user.id)
    current_mode = state.get("loop_mode", "off") if state else "off"
    next_mode = "off" if current_mode == "track" else "track"

    success, msg = await api_client.control_playback(room_id, user.id, "loop", {"mode": next_mode})
    if success:
        symbol = "🔁" if next_mode == "track" else "➡️"
        await message.reply(f"{symbol} Repeat mode set to: *{next_mode.upper()}*", parse_mode="Markdown")
    else:
        await message.reply(f"❌ {msg}")


async def _handle_dj_action(message: types.Message, action: str, success_text: str):
    chat = message.chat
    user = message.from_user

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    if not room:
        await message.reply("❌ Error connecting to room.")
        return

    room_id = room["id"]
    success, msg = await api_client.control_playback(room_id, user.id, action)
    if success:
        await message.reply(f"{success_text}")
    else:
        await message.reply(f"❌ {msg}")


@router.message(Command("lyrics"))
async def cmd_lyrics(message: types.Message):
    chat = message.chat
    user = message.from_user

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    if not room:
        await message.reply("❌ Error connecting to room.")
        return

    room_id = room["id"]
    state = await api_client.get_playback_state(room_id, user.id)
    if not state or not state.get("current_queue_item"):
        await message.reply("🔇 *Nothing is currently playing.*", parse_mode="Markdown")
        return

    track = state["current_queue_item"].get("track", {})
    title_str = clean_md(track.get("title", "Track"))
    status_msg = await message.reply(f"📜 Fetching lyrics for *{title_str}*...", parse_mode="Markdown")

    res = await api_client._request("GET", f"rooms/{room_id}/lyrics", headers=api_client._headers(user.id))
    if not res or res.status_code != 200:
        await status_msg.edit_text("❌ Lyrics currently unavailable for this track.")
        return

    data = res.json()
    plain = data.get("plain", "")
    if not plain and data.get("lines"):
        plain = "\n".join(l["text"] for l in data["lines"] if l.get("text"))

    if not plain:
        plain = f"Lyrics not available for {title_str}."

    if len(plain) > 3800:
        plain = plain[:3800] + "\n\n..."

    synced_badge = "⏱ *Synced Lyrics*" if data.get("synced") else "📝 *Plain Lyrics*"
    await status_msg.edit_text(
        f"🎵 *{title_str}* — {clean_md(track.get('artist', 'Artist'))}\n"
        f"{synced_badge}\n\n"
        f"{plain}",
        parse_mode="Markdown"
    )
