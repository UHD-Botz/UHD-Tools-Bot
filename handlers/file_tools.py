import os
import time
import zipfile
import rarfile
import shutil
from pyrogram import Client, filters
from config import Config
from utils.progress import progress_bar
from utils.anti_nsfw import is_nsfw  # <-- Naya Import

rarfile.UNRAR_TOOL = "unrar"

@Client.on_message(filters.command("unzip"))
async def unzip_file(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Please reply to a `.zip` or `.rar` file!**")

    doc = message.reply_to_message.document
    if is_nsfw(doc.file_name):
        return await message.reply("🚫 **NSFW Blocked!**")

    msg = await message.reply("⏳ **Downloading...**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading...")
    )
    
    extract_dir = f"{Config.DOWNLOAD_DIR}/extracted_{int(time.time())}"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        await msg.edit("⚙️ **Extracting...**")
        if doc.file_name.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        else:
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)

        # 🔥 NEW DEEP SCAN LOGIC: Har folder ke andar jaakar file dhundega
        files_sent = 0
        for root, dirs, files in os.walk(extract_dir):
            for file_name in files:
                # Faltu system files ko skip karo
                if "__MACOSX" in root or file_name.startswith('.'):
                    continue
                
                full_path = os.path.join(root, file_name)
                
                if is_nsfw(file_name):
                    await message.reply(f"🚫 **Skipped NSFW:** `{file_name}`")
                    continue

                start_time = time.time()
                try:
                    sent_msg = await client.send_document(
                        message.chat.id, 
                        full_path,
                        caption=f"📄 `{file_name}`",
                        progress=progress_bar,
                        progress_args=(msg, start_time, f"Uploading: {file_name}")
                    )
                    files_sent += 1
                    
                    if Config.LOG_CHANNEL:
                        await sent_msg.copy(Config.LOG_CHANNEL, caption=f"👤 By: {message.from_user.id}")
                except Exception as e:
                    print(f"Upload Error: {e}")

        await msg.delete()
        if files_sent > 0:
            await message.reply(f"✅ **Done! Sent {files_sent} files.**")
        else:
            await message.reply("❌ **No valid files found inside the archive!**")

    except Exception as e:
        await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        shutil.rmtree(extract_dir, ignore_errors=True)

@Client.on_message(filters.command("zip"))
async def zip_file(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Please reply to any file with /zip to compress it.**")

    doc = message.reply_to_message.document
    doc_name = doc.file_name or f"file_{int(time.time())}"
    
    # 🛡️ NSFW Check: File ko zip hone se pehle rok dega
    if is_nsfw(doc_name):
        return await message.reply("🚫 **NSFW Blocked:** This file contains restricted keywords.")

    if doc.file_size > 2000 * 1024 * 1024:
        return await message.reply("❌ **File is larger than 2GB (Telegram limit).**")

    msg = await message.reply("⏳ **Preparing to Download...**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading File to Compress...")
    )
    
    zip_path = f"{Config.DOWNLOAD_DIR}/{doc_name}.zip"

    try:
        await msg.edit("⚙️ **Compressing into ZIP... Please wait!**")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, arcname=doc_name)

        start_time = time.time()
        
        # User ko Zip file bhejo
        sent_msg = await client.send_document(
            message.chat.id, 
            zip_path,
            progress=progress_bar,
            progress_args=(msg, start_time, "Uploading Compressed ZIP...")
        )
        
        # 📡 Log Channel mein COPY karo
        if Config.LOG_CHANNEL:
            await sent_msg.copy(
                Config.LOG_CHANNEL,
                caption=f"🗜️ **Zipped File**\n👤 By: {message.from_user.mention} (`{message.from_user.id}`)\n📄 Original: `{doc_name}`"
            )
            
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ **Error compressing file:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(zip_path): os.remove(zip_path)
