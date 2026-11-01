import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import bot_settings
from bot.handlers.general import router as general_router
from bot.handlers.playback import router as playback_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("BeatWaveBot")


async def main():
    logger.info("Initializing BeatWave Telegram Bot...")
    bot = Bot(
        token=bot_settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    dp.include_router(general_router)
    dp.include_router(playback_router)

    # Register native Telegram command menu
    try:
        await bot.set_my_commands([
            types.BotCommand(command="start", description="🌊 Open BeatWave & join room"),
            types.BotCommand(command="play", description="🎵 Search and queue a song (/play <title>)"),
            types.BotCommand(command="nowplaying", description="🎧 Current song & live progress bar"),
            types.BotCommand(command="queue", description="📜 View upcoming playlist queue"),
            types.BotCommand(command="room", description="🚀 Launch the Liquid Glass Mini App"),
            types.BotCommand(command="theme", description="🎨 Choose your visual glass theme"),
            types.BotCommand(command="dj", description="👑 View DJ status & room controls"),
            types.BotCommand(command="pause", description="⏸ Pause playback (DJ)"),
            types.BotCommand(command="resume", description="▶ Resume playback (DJ)"),
            types.BotCommand(command="skip", description="⏭ Skip to next track (DJ)"),
            types.BotCommand(command="loop", description="🔁 Toggle repeat mode (DJ)"),
            types.BotCommand(command="stop", description="⏹ Stop playback (DJ)"),
            types.BotCommand(command="help", description="ℹ️ Command guide & features"),
        ])
        logger.info("Native Telegram bot command menu registered successfully.")
    except Exception as e:
        logger.warning(f"Could not register bot commands menu: {e}")

    logger.info("BeatWave Bot started listening...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
