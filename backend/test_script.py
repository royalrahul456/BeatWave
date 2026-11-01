import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import aiosqlite

async def f():
    async with aiosqlite.connect("test.db") as db:
        await db.execute("SELECT 1")
        print("aiosqlite works with WindowsSelectorEventLoopPolicy!")

if __name__ == "__main__":
    asyncio.run(f())
