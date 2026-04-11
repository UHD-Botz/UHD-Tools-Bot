import os
import time
import subprocess # Direct system commands ke liye
from pyrogram import Client, filters
from config import Config
from database.db import db
from utils.progress import progress_bar
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON, FSUB_TEXT, FSUB_BUTTON

@Client.on_message(filters.command("v2a"))
async def video_to_audio(client, message):
    user_id = message.from_user.id
    status = await is_limited(user_id, "v2a", client)
    if status == "FSUB_REQUIRED": return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True: return await message.reply(LIMIT_TEXT.format(cmd="v2a"), reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message or not message.reply_to_message.video:
        return await message.reply("⚠️ **Reply to a Video with `/v2a`**")

    msg = await message.reply("⏳ **Downloading Video...**")
    file_path = await message.reply_to_message.download(progress=progress_bar, progress_args=(msg, time.time(), "Downloading..."))
    out_path = f"{Config.DOWNLOAD_DIR}/audio_{user_id}.mp3"
    
    try:
        await msg.edit("⚙️ **Extracting Audio (Lite Mode)...**")
        # System command se extraction (Very Low RAM Usage)
        cmd = ["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", out_path, "-y"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        await msg.edit("📤 **Uploading MP3...**")
        await client.send_audio(message.chat.id, out_path, caption="🎵 **Audio Extracted!**\n\n🛡️ @UHDBots")
        await msg.delete()
        await db.increment_usage(user_id, "v2a")
    except Exception as e: await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)

@Client.on_message(filters.command("screenshot"))
async def get_screenshot(client, message):
    user_id = message.from_user.id
    status = await is_limited(user_id, "screenshot", client)
    if status == "FSUB_REQUIRED": return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True: return await message.reply(LIMIT_TEXT.format(cmd="screenshot"), reply_markup=LIMIT_BUTTON)

    if len(message.command) < 2 or not message.reply_to_message or not message.reply_to_message.video:
        return await message.reply("⚠️ **Usage:** Reply to Video with `/screenshot 00:05` (Time in mm:ss)")

    time_str = message.command[1]
    msg = await message.reply("⏳ **Taking Screenshot...**")
    file_path = await message.reply_to_message.download()
    out_path = f"{Config.DOWNLOAD_DIR}/ss_{user_id}.jpg"
    
    try:
        # Fast screenshot extract using ffmpeg
        cmd = ["ffmpeg", "-ss", time_str, "-i", file_path, "-frames:v", "1", "-q:v", "2", out_path, "-y"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        await client.send_photo(message.chat.id, out_path, caption=f"📸 **Screenshot at {time_str}**\n\n🛡️ @UHDBots")
        await msg.delete()
        await db.increment_usage(user_id, "screenshot")
    except Exception as e: await msg.edit(f"❌ **Invalid Time or Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)
