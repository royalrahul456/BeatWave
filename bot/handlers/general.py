from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import bot_settings
from bot.services.api_client import api_client

router = Router()


def get_mini_app_keyboard(room_id: str, text: str = "🌊 Launch BeatWave App") -> InlineKeyboardMarkup:
    url = f"{bot_settings.MINI_APP_URL}?room_id={room_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    web_app=WebAppInfo(url=url)
                )
            ]
        ]
    )


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    chat = message.chat
    user = message.from_user

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    room_id = room["id"] if room else "default"

    text = (
        "🌊 *Welcome to BeatWave* — Synchronized Music Room\n\n"
        "Listen to music together in real-time with an ultra-premium Apple Liquid Glass Mini App.\n\n"
        "✨ *Highlights:*\n"
        "• 🎵 *Millions of Real Songs*: Stream high-res audio from YouTube & Spotify\n"
        "• 🎨 *Dynamic Liquid Glass*: 5 luxury themes (Purple, Cyan, Emerald, Amber, Silver)\n"
        "• 🎧 *Synchronized Audio*: Plays in each member's client — no voice assistant needed!\n"
        "• 👑 *Fair Roles*: Everyone can request tracks; DJ controls playback\n\n"
        "👇 *Tap below to launch the Mini App, or type a song title to search!*"
    )

    kb = get_mini_app_keyboard(room_id)
    await message.reply(text, reply_markup=kb, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    chat = message.chat
    user = message.from_user

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    room_id = room["id"] if room else "default"

    help_text = (
        "🎵 *BeatWave Command Guide*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 *Member Commands:*\n"
        "• `/play <query>` — Search & queue any song (e.g. `/play Starboy`)\n"
        "• `/nowplaying` (or `/np`) — View current song, progress bar & artwork\n"
        "• `/queue` — View upcoming playlist queue\n"
        "• `/room` — Get room link & launch the Mini App\n"
        "• `/theme` — Choose your Apple Liquid Glass color theme\n"
        "• `/dj` — View the current DJ & control permissions\n\n"
        "👑 *DJ & Admin Controls:*\n"
        "• `/pause` — Pause current playback\n"
        "• `/resume` — Resume playback\n"
        "• `/skip` — Skip to next queued song\n"
        "• `/loop` — Toggle repeat mode on/off\n"
        "• `/stop` — Stop music playback\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *Tip:* In private DMs, simply send any song name to search directly!"
    )
    kb = get_mini_app_keyboard(room_id)
    await message.reply(help_text, reply_markup=kb, parse_mode="Markdown")


@router.message(Command("room"))
async def cmd_room(message: types.Message):
    chat = message.chat
    user = message.from_user

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    if not room:
        await message.reply("❌ Failed to connect to music room. Please try again.")
        return

    room_id = room["id"]
    status = room.get("status", "idle").upper()
    members_count = room.get("members_count", 1)

    text = (
        f"🎧 *BeatWave Room:* {title}\n"
        f"📊 *Status:* `{status}`\n"
        f"👥 *Listeners in Room:* `{members_count}`\n\n"
        f"Tap below to launch your synchronized Liquid Glass player!"
    )

    kb = get_mini_app_keyboard(room_id, "🚀 Open Room in Mini App")
    await message.reply(text, reply_markup=kb, parse_mode="Markdown")


@router.message(Command("theme"))
async def cmd_theme(message: types.Message):
    chat = message.chat
    user = message.from_user

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    room_id = room["id"] if room else "default"

    text = (
        "🎨 *Apple Liquid Glass Visual Themes*\n\n"
        "Choose an optical theme palette for your player:\n\n"
        "• 🟣 *Midnight Purple* — Deep violet with neon luminescence\n"
        "• 🌐 *Cyber Cyan* — Signature BeatWave electric cyan glow\n"
        "• 🌲 *Matrix Emerald* — Synth electric green\n"
        "• 🌅 *Sunset Amber* — Solar gold & warm flare\n"
        "• 🪞 *Vision Silver* — Apple VisionOS pure crystal glass\n\n"
        "Tap below to launch the Mini App and apply themes instantly in the *Profile & Themes* tab!"
    )

    kb = get_mini_app_keyboard(room_id, "🎨 Change Theme in Mini App")
    await message.reply(text, reply_markup=kb, parse_mode="Markdown")


@router.message(Command("dj"))
async def cmd_dj(message: types.Message):
    chat = message.chat
    user = message.from_user

    title = chat.title or user.full_name or "BeatWave Room"
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    if not room:
        await message.reply("❌ Failed to retrieve room details.")
        return

    current_dj = room.get("current_dj")
    is_user_dj = room.get("is_dj", False)

    if current_dj:
        dj_name = current_dj.get("display_name") or current_dj.get("username") or f"User {current_dj.get('telegram_user_id')}"
        status_line = f"🎧 *Current DJ:* {dj_name}"
    else:
        status_line = "🎧 *No designated DJ.* Room creator & group admins manage playback."

    your_role = "👑 *You are the DJ!* You have full control." if is_user_dj else "👤 *You are a Listener.* You can request songs."

    text = (
        f"{status_line}\n\n"
        f"Your Role: {your_role}\n\n"
        f"• *Everyone* can search and queue songs with `/play <song>`\n"
        f"• *DJ* controls playback (`/pause`, `/resume`, `/skip`, `/loop`, `/stop`)\n"
    )

    kb = get_mini_app_keyboard(room["id"])
    await message.reply(text, reply_markup=kb, parse_mode="Markdown")
