from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import bot_settings
from bot.services.api_client import api_client

router = Router()


def get_mini_app_keyboard(room_id: str, text: str = "🌊 Launch BeatWave App", is_group: bool = False) -> InlineKeyboardMarkup:
    url = f"{bot_settings.MINI_APP_URL}?room_id={room_id}"
    if is_group:
        app_button = InlineKeyboardButton(text=text, url=f"https://t.me/{bot_settings.BOT_USERNAME}?start={room_id}")
    else:
        app_button = InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))
    return InlineKeyboardMarkup(inline_keyboard=[[app_button]])


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    chat = message.chat
    user = message.from_user
    user_name = user.first_name if user and user.first_name else "Friend"

    args = message.text.split(maxsplit=1) if message.text else []
    target_param = args[1].strip() if len(args) > 1 else None

    bot_info = await message.bot.get_me()
    bot_username = bot_info.username or bot_settings.BOT_USERNAME or "BeatWave_app"
    add_group_url = f"https://t.me/{bot_username}?startgroup=true"

    # User clicked a group link: /start <room_id>
    if target_param:
        target_room = await api_client.get_room(target_param, user.id)
        if target_room:
            room_id = target_room["id"]
            group_title = target_room.get("group_title") or "Group Room"
            app_url = f"{bot_settings.MINI_APP_URL}?room_id={room_id}"

            caption = (
                f"🌊 *Connected to Group Music Room!*\n\n"
                f"👥 *Room:* {group_title}\n"
                f"🎧 You are now synced with this group's active audio stream.\n"
                f"🔊 Any tracks played by the group will stream in your client.\n\n"
                f"Tap below to launch the Liquid Glass Player:"
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🌊 Open Group Player", web_app=WebAppInfo(url=app_url)),
                    ],
                    [
                        InlineKeyboardButton(text="➕ Add BeatWave to Group", url=add_group_url),
                        InlineKeyboardButton(text="ℹ️ Help Guide", callback_data="help_menu"),
                    ]
                ]
            )
            cover_photo = "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=1200&q=80"
            try:
                await message.answer_photo(photo=cover_photo, caption=caption, reply_markup=kb, parse_mode="Markdown")
            except Exception:
                await message.reply(caption, reply_markup=kb, parse_mode="Markdown")
            return

    # Regular /start without specific room parameter
    title = chat.title or (user.full_name if user else "BeatWave Room")
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    room_id = room["id"] if room else "default"

    app_url = f"{bot_settings.MINI_APP_URL}?room_id={room_id}"

    caption = (
        "✨ ╭── [ 🍭 ꜱ ʏ ꜱ ᴛ ᴇ ᴍ  ɪ ɴ ɪ ᴛ ɪ ᴀ ᴛ ᴇ ᴅ 🐇 ]\n"
        "│\n"
        f"├── 🍦 ⇛ ʜᴇʏ {user_name} ,\n"
        "├── 🩷 ⇛ ɪ ᴀᴍ ʙᴇᴀᴛᴡᴀᴠᴇ ˼ , ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ\n"
        "├── 😽 ⇛ ᴍᴜꜱɪᴄ ᴇɴɢɪɴᴇ ꜰᴏʀ ᴛᴇʟᴇɢʀᴀᴍ !\n"
        "│\n"
        "├── [ 🎁 ᴄ ᴏ ʀ ᴇ  ꜰ ᴇ ᴀ ᴛ ᴜ ʀ ᴇ ꜱ ]\n"
        "├── 📎 ⇛ ᴜʟᴛʀᴀ-ꜰᴀꜱᴛ 320ᴋʙᴘꜱ ꜱᴛʀᴇᴀᴍɪɴɢ\n"
        "├── 📎 ⇛ 24x7 ꜱᴇʀᴠᴇʀ ᴜᴘᴛɪᴍᴇ & ᴢᴇʀᴏ-ʟᴀɢ\n"
        "├── 🎁 ⇛ ꜱʏɴᴄʜʀᴏɴɪᴢᴇᴅ ʟɪQᴜɪᴅ ɢʟᴀꜱꜱ ᴘʟᴀʏᴇʀ\n"
        "├── 🎩 ⇛ ᴅᴊ ʀᴏᴏᴍ ᴄᴏɴᴛʀᴏʟꜱ & ᴀᴜᴛᴏ-Qᴜᴇᴜᴇ\n"
        "│\n"
        "🌸 ╰── ᴛᴀᴘ ʙᴇʟᴏᴡ ᴛᴏ ʟᴀᴜɴᴄʜ ᴏʀ ᴀᴅᴅ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ !"
    )

    is_group = chat.type in ("group", "supergroup", "channel")
    if is_group:
        app_button = InlineKeyboardButton(text="🌊 Open BeatWave App", url=app_url)
    else:
        app_button = InlineKeyboardButton(text="🌊 Open BeatWave App", web_app=WebAppInfo(url=app_url))

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                app_button,
            ],
            [
                InlineKeyboardButton(text="➕ Add BeatWave to Group", url=add_group_url),
                InlineKeyboardButton(text="ℹ️ Help Guide", callback_data="help_menu"),
            ]
        ]
    )

    cover_photo = "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=1200&q=80"
    try:
        await message.answer_photo(
            photo=cover_photo,
            caption=caption,
            reply_markup=kb
        )
    except Exception:
        await message.reply(caption, reply_markup=kb)


@router.callback_query(F.data == "help_menu")
async def cb_help_menu(query: types.CallbackQuery):
    chat = query.message.chat
    user = query.from_user
    title = chat.title or (user.full_name if user else "BeatWave Room")
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    room_id = room["id"] if room else "default"

    help_text = (
        "🎵 *BeatWave Command Guide*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 *Member Commands:*\n"
        "• `/play <query>` — Search & queue any song (e.g. `/play Zingaat`)\n"
        "• `/nowplaying` (or `/np`) — View current song, progress bar & artwork\n"
        "• `/queue` — View upcoming playlist queue\n"
        "• `/room` — Launch your synchronized Mini App\n"
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
    kb = get_mini_app_keyboard(room_id, "🌊 Open BeatWave App")
    await query.message.answer(help_text, reply_markup=kb, parse_mode="Markdown")
    await query.answer()


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    chat = message.chat
    user = message.from_user

    title = chat.title or (user.full_name if user else "BeatWave Room")
    room = await api_client.get_or_create_room(chat.id, user.id, title)
    room_id = room["id"] if room else "default"

    help_text = (
        "🎵 *BeatWave Command Guide*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 *Member Commands:*\n"
        "• `/play <query>` — Search & queue any song (e.g. `/play Zingaat`)\n"
        "• `/nowplaying` (or `/np`) — View current song, progress bar & artwork\n"
        "• `/queue` — View upcoming playlist queue\n"
        "• `/room` — Launch the Mini App\n"
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

    title = chat.title or (user.full_name if user else "BeatWave Room")
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

    title = chat.title or (user.full_name if user else "BeatWave Room")
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

    title = chat.title or (user.full_name if user else "BeatWave Room")
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
