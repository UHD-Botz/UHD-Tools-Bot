import time
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from config import Config
from database.db import db

# Helper function for Uptime
def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

@Client.on_message(filters.command("ping"))
async def ping_cmd(client, message):
    start_t = time.time()
    rm = await message.reply("Pong!")
    end_t = time.time()
    await rm.edit(f"🏓 **Ping:** `{round((end_t - start_t) * 1000, 2)} ms`")

@Client.on_message(filters.command("uptime"))
async def uptime_cmd(client, message):
    msg = await message.reply("⏳ Fetching Uptime...")
    
    # NOTE: Telegram limits API edits. Lagatar edit karne se bot ban/FloodWait ho sakta hai.
    # Isliye ye 15 sec ke gap par 4 baar (1 minute) tak live update dega aur fir ruk jayega.
    for _ in range(4):
        try:
            uptime_seconds = int(time.time() - Config.BOT_START_TIME)
            uptime_string = get_readable_time(uptime_seconds)
            await msg.edit(
                f"📡 **Bot Uptime Live:**\n"
                f"⏱️ `{uptime_string}`\n\n"
                f"*(Updates every 15s for 1 min to prevent Telegram limits)*"
            )
            await asyncio.sleep(15)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            break

@Client.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply("⚠️ **Reply to a message to broadcast it.**")

    msg = await message.reply("⏳ **Starting Broadcast...**")
    users = await db.get_all_users()
    
    successful = 0
    failed = 0

    for user in users:
        try:
            await message.reply_to_message.copy(chat_id=user['_id'])
            successful += 1
            await asyncio.sleep(0.1) # Safe delay to prevent FloodWait limit
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_to_message.copy(chat_id=user['_id'])
            successful += 1
        except Exception:
            failed += 1 # User blocked bot or account deleted

    await msg.edit(
        f"📣 **Broadcast Completed!**\n\n"
        f"✅ Successful: `{successful}`\n"
        f"❌ Failed/Blocked: `{failed}`\n"
        f"👥 Total Users: `{len(users)}`"
    )
