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
        return await message.reply("⚠️ **Please reply to a `.zip` or `.rar` file with /unzip**")

    doc = message.reply_to_message.document
    
    # 🛡️ NSFW Check: Main Archive Name
    if is_nsfw(doc.file_name):
        return await message.reply("🚫 **NSFW Blocked:** This file name contains restricted keywords.")

    if not doc.file_name.endswith(('.zip', '.rar')):
        return await message.reply("❌ **Only .zip and .rar files are supported!**")

    if doc.file_size > 2000 * 1024 * 1024:
        return await message.reply("❌ **File is larger than 2GB (Telegram limit).**")

    msg = await message.reply("⏳ **Preparing to Download...**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading Archive...")
    )
    
    extract_dir = f"{Config.DOWNLOAD_DIR}/extracted_{int(time.time())}"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        await msg.edit("⚙️ **Extracting files... Please wait!**")
        
        if doc.file_name.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif doc.file_name.endswith('.rar'):
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)

        extracted_files = os.listdir(extract_dir)
        if not extracted_files:
            return await msg.edit("❌ **Archive is empty or corrupted!**")
        
        for file_name in extracted_files:
            # 🛡️ NSFW Check: Inner Files (Zip ke andar ki files check karega)
            if is_nsfw(file_name):
                await message.reply(f"🚫 **Skipped:** `{file_name}` (NSFW Content Detected)")
                continue

            full_path = os.path.join(extract_dir, file_name)
            if os.path.isfile(full_path):
                start_time = time.time()
                
                # User ko file bhejo
                sent_msg = await client.send_document(
                    message.chat.id, 
                    full_path,
                    progress=progress_bar,
                    progress_args=(msg, start_time, f"Uploading: {file_name}")
                )
                
                # 📡 Log Channel mein COPY karo (Bandwidth bachega)
                if Config.LOG_CHANNEL:
                    await sent_msg.copy(
                        Config.LOG_CHANNEL,
                        caption=f"📦 **Extracted File**\n👤 By: {message.from_user.mention} (`{message.from_user.id}`)\n📄 File: `{file_name}`"
                    )
        
        await msg.delete()
        await message.reply("✅ **Extraction & Upload Complete!**")
    except Exception as e:
        await msg.edit(f"❌ **Error extracting file:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(extract_dir): shutil.rmtree(extract_dir)


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
