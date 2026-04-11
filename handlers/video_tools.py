import os
import time
from pyrogram import Client, filters
from moviepy.editor import VideoFileClip
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
        await msg.edit("⚙️ **Extracting Audio...**")
        video = VideoFileClip(file_path)
        video.audio.write_audiofile(out_path, logger=None) # Silent extraction
        
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
        # Simple ffmpeg wrapper via moviepy
        clip = VideoFileClip(file_path)
        # Convert mm:ss to seconds
        min_sec = time_str.split(":")
        time_sec = int(min_sec[0]) * 60 + int(min_sec[1])
        
        clip.save_frame(out_path, t=time_sec)
        await client.send_photo(message.chat.id, out_path, caption=f"📸 **Screenshot at {time_str}**\n\n🛡️ @UHDBots")
        await msg.delete()
        await db.increment_usage(user_id, "screenshot")
    except Exception as e: await msg.edit(f"❌ **Error or Invalid Time:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)
