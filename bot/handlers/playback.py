from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.services.api_client import api_client
from bot.handlers.general import get_mini_app_keyboard
from bot.config import bot_settings

router = Router()


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
        await message.reply(
            "🔇 *Nothing is currently playing.*\n\n"
            "Use `/play <song>` or open the Mini App to start the stream!",
            reply_markup=get_mini_app_keyboard(room_id),
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
        f"🎵 *{track.get('title')}*\n"
        f"👤 *Artist:* {track.get('artist', 'Artist')}\n"
        f"🙋 *Requested by:* {req_name}\n\n"
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

    # Mini App link
    app_url = f"{bot_settings.MINI_APP_URL}?room_id={room_id}"
    buttons.append([
        InlineKeyboardButton(text="🌊 Open Liquid Glass Player", web_app=WebAppInfo(url=app_url))
    ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply(text, reply_markup=kb, parse_mode="Markdown")


# --- /play <query> ---

@router.message(Command("play"))
async def cmd_play(message: types.Message):
    chat = message.chat
    user = message.from_user

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            "ℹ️ *Usage:* `/play <song title or artist>`\n"
            "• Example: `/play Starboy The Weeknd`\n"
            "• Example: `/play Blinding Lights`",
            parse_mode="Markdown"
        )
        return

    query = args[1].strip()
    await _search_and_display(message, chat, user, query)


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
    status_msg = await message.reply(f"🔍 Searching catalogue for *{query}*...", parse_mode="Markdown")

    results = await api_client.search_tracks(room_id, user.id, query)
    if not results:
        await status_msg.edit_text(f"❌ No tracks found for *{query}*. Please try another search term.", parse_mode="Markdown")
        return

    buttons = []
    for track in results[:5]:
        title_short = track['title'][:26]
        dur = format_duration(track.get('duration_ms', 0))
        btn_text = f"▶ {title_short} ({dur})"
        cb_data = f"req:{track['provider']}:{track['provider_track_id']}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=cb_data)])

    app_url = f"{bot_settings.MINI_APP_URL}?room_id={room_id}"
    buttons.append([InlineKeyboardButton(text="🌊 Open Mini App", web_app=WebAppInfo(url=app_url))])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await status_msg.edit_text(
        f"🎵 *Search Results for* \"_{query}_\":\n\n"
        f"Tap any track below to queue it in the room:",
        reply_markup=kb,
        parse_mode="Markdown"
    )


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

    await callback.message.edit_text(
        f"✅ *Added to Room Queue!* 🎶\n\n"
        f"🎵 *{track.get('title')}*\n"
        f"👤 *Artist:* {track.get('artist', 'Artist')} • `{dur}`\n"
        f"🙋 *Queued by:* {user.full_name}\n\n"
        f"Tap below to listen in sync with the room:",
        reply_markup=get_mini_app_keyboard(room_id),
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

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text=toggle_label, callback_data=f"dj:{toggle_action}"),
                    InlineKeyboardButton(text="⏭ Skip", callback_data="dj:skip")
                ],
                [
                    InlineKeyboardButton(text="🌊 Open Liquid Glass Player", web_app=WebAppInfo(url=f"{bot_settings.MINI_APP_URL}?room_id={room_id}"))
                ]
            ])

            await callback.message.edit_text(
                f"🎧 *Now Playing on BeatWave:*\n\n"
                f"🎵 *{track.get('title')}*\n"
                f"👤 *Artist:* {track.get('artist', 'Artist')}\n\n"
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

    if not queue:
        await message.reply(
            "📭 *The queue is empty!*\n\n"
            "Use `/play <song>` or open the Mini App to request tracks.",
            reply_markup=get_mini_app_keyboard(room_id, "🎵 Search & Add Songs"),
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
        lines.append(f"{prefix} *{track.get('title')}* — {track.get('artist', 'Artist')} `({dur})`")

    text = "\n".join(lines)
    await message.reply(text, reply_markup=get_mini_app_keyboard(room_id), parse_mode="Markdown")


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
