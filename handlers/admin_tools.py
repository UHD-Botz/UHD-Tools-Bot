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

@Client.on_message(filters.command("stats") & filters.user(Config.ADMIN_ID))
async def stats_cmd(client, message):
    msg = await message.reply("⏳ Fetching Statistics...")
    try:
        total_users = await db.total_users_count()
        await msg.edit(
            f"📊 **Bot Statistics:**\n\n"
            f"👥 Total Users in Database: `{total_users}`"
        )
    except Exception as e:
        await msg.edit(f"❌ Error fetching stats: `{e}`")

@Client.on_message(filters.command("uptime"))
async def uptime_cmd(client, message):
    msg = await message.reply("⏳ Fetching Uptime...")
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
            await asyncio.sleep(0.1)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_to_message.copy(chat_id=user['_id'])
            successful += 1
        except Exception:
            failed += 1

    await msg.edit(
        f"📣 **Broadcast Completed!**\n\n"
        f"✅ Successful: `{successful}`\n"
        f"❌ Failed/Blocked: `{failed}`\n"
        f"👥 Total Users: `{len(users)}`"
    )

# --- MANUAL PREMIUM CONTROLS ---

@Client.on_message(filters.command("addpremium") & filters.user(Config.ADMIN_ID))
async def add_premium_manual(client, message):
    if len(message.command) < 2:
        return await message.reply("⚠️ **Usage:** `/addpremium <user_id>`")
    
    try:
        user_id = int(message.command[1])
        await db.set_premium(user_id, True)
        await message.reply(f"✅ **User `{user_id}` has been promoted to Premium!**")
        try:
            await client.send_message(user_id, "🎉 **Congratulations!** Admin has manually activated your Premium. Enjoy unlimited access!")
        except: pass
    except ValueError:
        await message.reply("❌ Invalid User ID. Make sure it's a number.")

@Client.on_message(filters.command("removepremium") & filters.user(Config.ADMIN_ID))
async def remove_premium_manual(client, message):
    if len(message.command) < 2:
        return await message.reply("⚠️ **Usage:** `/removepremium <user_id>`")
    
    try:
        user_id = int(message.command[1])
        await db.set_premium(user_id, False)
        await message.reply(f"❌ **User `{user_id}` Premium has been removed.**")
        try:
            await client.send_message(user_id, "⚠️ **Notice:** Your Premium access has been removed by the Admin.")
        except: pass
    except ValueError:
        await message.reply("❌ Invalid User ID. Make sure it's a number.")

# --- PAYMENT VERIFICATION CALLBACKS ---

@Client.on_callback_query(filters.regex(r"^(approve|reject)_(\d+)$"))
async def admin_verify_cb(client, callback_query):
    action, user_id = callback_query.data.split("_")
    user_id = int(user_id)

    if callback_query.from_user.id != Config.ADMIN_ID:
        return await callback_query.answer("Only Owner can do this!", show_alert=True)

    if action == "approve":
        await db.set_premium(user_id, True)
        await callback_query.message.edit_text(f"✅ **User {user_id} Approved!**")
        try:
            await client.send_message(user_id, "🎉 **Payment Verified!** Your Premium has been activated. Enjoy Unlimited Access!")
        except: pass
    
    elif action == "reject":
        await callback_query.message.edit_text(f"❌ **User {user_id} Rejected!**")
        try:
            await client.send_message(user_id, "❌ **Payment Verification Failed!** Your UTR was invalid or amount was incorrect. Contact @UHD_ContactBot for help.")
        except: pass
