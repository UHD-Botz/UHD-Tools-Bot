import string
import random
import whois
from pyrogram import Client, filters
from database.db import db
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON, FSUB_TEXT, FSUB_BUTTON

@Client.on_message(filters.command("password"))
async def gen_pass(client, message):
    user_id = message.from_user.id
    status = await is_limited(user_id, "password", client)
    if status == "FSUB_REQUIRED": return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True: return await message.reply(LIMIT_TEXT.format(cmd="password"), reply_markup=LIMIT_BUTTON)

    length = 16 # Default strong length
    if len(message.command) > 1 and message.command[1].isdigit():
        length = min(int(message.command[1]), 32) # Max 32 chars

    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(chars) for _ in range(length))
    
    await message.reply(f"🔐 **Your Secure Password:**\n\n`{password}`\n\n_(Tap to copy)_")
    await db.increment_usage(user_id, "password")

@Client.on_message(filters.command("whois"))
async def whois_lookup(client, message):
    user_id = message.from_user.id
    status = await is_limited(user_id, "whois", client)
    if status == "FSUB_REQUIRED": return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True: return await message.reply(LIMIT_TEXT.format(cmd="whois"), reply_markup=LIMIT_BUTTON)

    if len(message.command) < 2:
        return await message.reply("⚠️ **Usage:** `/whois google.com`")

    domain = message.command[1].replace("https://", "").replace("http://", "").split("/")[0]
    msg = await message.reply("🔎 **Fetching Domain Info...**")
    
    try:
        w = whois.whois(domain)
        text = (
            f"🌐 **WHOIS INFO: {domain}**\n\n"
            f"🏢 **Registrar:** `{w.registrar}`\n"
            f"📅 **Creation Date:** `{w.creation_date}`\n"
            f"⏳ **Expiration Date:** `{w.expiration_date}`\n"
            f"🌍 **Country:** `{w.country}`\n"
        )
        await msg.edit(text)
        await db.increment_usage(user_id, "whois")
    except Exception as e:
        await msg.edit("❌ **Could not fetch details. Check domain format.**")
