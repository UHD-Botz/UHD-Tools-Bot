import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON

# --- CUSTOM PROGRESS BAR ---
async def progress_bar(current, total, ud_type, message, start_time):
    now = time.time()
    diff = now - start_time
    # Update every 3 seconds to avoid FloodWait
    if round(diff % 3.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        elapsed_time = round(diff)
        time_to_completion = round((total - current) / speed) if speed > 0 else 0
        
        # Format size
        def humanbytes(size):
            if not size: return ""
            power = 2**10
            n = 0
            Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
            while size > power:
                size /= power
                n += 1
            return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

        progress_str = f"[{'█' * int(percentage // 5)}{'░' * (20 - int(percentage // 5))}] {round(percentage, 2)}%"
        
        text = (
            f"⏳ **{ud_type}**\n\n"
            f"📊 **Progress:** {progress_str}\n"
            f"📦 **Size:** {humanbytes(current)} / {humanbytes(total)}\n"
            f"🚀 **Speed:** {humanbytes(speed)}/s\n"
            f"⏱️ **ETA:** {time_to_completion} seconds"
        )
        try:
            await message.edit_text(text)
        except:
            pass

# --- RENAMER & META-TAGGER COMMAND ---

@Client.on_message(filters.command("rename"))
async def rename_file(client, message):
    user_id = message.from_user.id
    
    # 1. LIMIT & PREMIUM CHECK (Tujhe ameer banane ka jugaad 🤑)
    limit_status = await is_limited(user_id, "rename", client)
    if limit_status == "FSUB_REQUIRED":
        return # FSub message is handled in limit_check
    if limit_status is True:
        return await message.reply(
            LIMIT_TEXT.format(cmd="rename"), 
            reply_markup=LIMIT_BUTTON
        )

    # 2. CHECK IF REPLIED TO A FILE
    if not message.reply_to_message or not (message.reply_to_message.document or message.reply_to_message.video):
        return await message.reply("⚠️ **Kaise use karein?**\nKisi bhi Video ya File ko reply karke likho:\n`/rename New Movie Name`")

    # 3. GET NEW NAME
    if len(message.command) < 2:
        return await message.reply("⚠️ **Naya naam toh daal bhai!**\nExample: `/rename Avengers Endgame 1080p`")

    # User ka custom name (Forced Prefix lagana)
    user_custom_name = message.text.split(None, 1)[1]
    
    # Original file ki details
    media = message.reply_to_message.document or message.reply_to_message.video
    file_size = media.file_size
    
    # 2GB File Limit Check for Bot API
    if file_size > 2000000000: # Approx 2GB
        return await message.reply("❌ **File size 2GB se zyada hai!** Telegram Bots sirf 2GB tak upload kar sakte hain.")

    # Original Extension nikalna (jaise .mkv ya .mp4)
    original_name = getattr(media, "file_name", "video.mp4")
    ext = os.path.splitext(original_name)[1]
    if not ext:
        ext = ".mkv" # Default to mkv if no extension found

    # 🔥 THE UN-REMOVABLE PREFIX
    PREFIX = "(@UHDBots)"
    
    # Agar user ne oversmart banke khud prefix dala hai, toh usko remove karke apna lagao (Double prefix na ho)
    clean_name = user_custom_name.replace(PREFIX, "").strip()
    
    # Final Output Name
    final_filename = f"{PREFIX} {clean_name}{ext}"
    
    # Paths setup
    download_path = f"downloads/{message.message_id}_input{ext}"
    output_path = f"downloads/{message.message_id}_output{ext}"

    status_msg = await message.reply("📥 **Downloading file...** Please wait.")

    try:
        # --- 4. DOWNLOAD FILE ---
        start_time = time.time()
        dl_path = await client.download_media(
            message.reply_to_message,
            file_name=download_path,
            progress=progress_bar,
            progress_args=("Downloading...", status_msg, start_time)
        )

        if not dl_path:
            return await status_msg.edit_text("❌ **Download fail ho gaya!**")

        await status_msg.edit_text("⚙️ **Processing MetaData & Renaming...**\n*VLC/MX Player tags update ho rahe hain...*")

        # --- 5. FFMPEG META-TAGGER (MAGIC HAPPENS HERE) ---
        # Ye command file ko bina quality loss ke (copy stream) re-pack karega aur MX Player/VLC ke tags set karega
        ffmpeg_cmd = [
            "ffmpeg", "-i", download_path,
            "-map", "0", "-c", "copy",
            "-metadata", f"title={PREFIX} {clean_name}",               # Main Title
            "-metadata:s:a", f"title={PREFIX} Audio",                 # Audio Track Meta
            "-metadata:s:s", f"title={PREFIX} Sub",                   # Subtitle Track Meta
            "-metadata", f"description=Downloaded from {PREFIX}",     # Description
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        # Agar output file nahi bani toh matlab kuch error aaya (e.g. mkv file mein error)
        if not os.path.exists(output_path):
            # Fallback: Agar FFmpeg fail hota hai, toh simply file ko rename karke upload kar do
            os.rename(download_path, output_path)
            await status_msg.edit_text("⚠️ *MetaData edit nahi ho paya, par file Rename ho gayi hai. Uploading...*")

        # --- 6. UPLOAD THE FILE ---
        await status_msg.edit_text("📤 **Uploading New File...**")
        start_time = time.time()
        
        await client.send_document(
            chat_id=message.chat.id,
            document=output_path,
            file_name=final_filename,
            caption=f"📁 **File:** `{final_filename}`\n\n⚡ **Powered by {PREFIX}**",
            progress=progress_bar,
            progress_args=("Uploading...", status_msg, start_time)
        )

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ **Error aagaya:** `{e}`")

    finally:
        # --- 7. CLEANUP (SERVER RAM Bachaao) ---
        if os.path.exists(download_path):
            os.remove(download_path)
        if os.path.exists(output_path):
            os.remove(output_path)
