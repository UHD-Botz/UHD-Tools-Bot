import os
import time
import zipfile
import rarfile
import shutil
import asyncio
from pyrogram import Client, filters
from config import Config
from database.db import db
from utils.progress import progress_bar
from utils.anti_nsfw import is_nsfw
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON

rarfile.UNRAR_TOOL = "unrar"

# Active tasks track karne ke liye
active_tasks = {}

@Client.on_message(filters.command("cancel"))
async def cancel_task(client, message):
    user_id = message.from_user.id
    if user_id in active_tasks:
        active_tasks[user_id].cancel()
        del active_tasks[user_id]
        await message.reply("⛔ **Process Cancelled Successfully!**")
    else:
        await message.reply("⚠️ Tera koi active process nahi chal raha hai.")

# --- UNZIP HANDLER ---
@Client.on_message(filters.command("unzip"))
async def unzip_handler(client, message):
    user_id = message.from_user.id
    
    # 🚨 LIMIT CHECK
    if await is_limited(user_id):
        return await message.reply(LIMIT_TEXT, reply_markup=LIMIT_BUTTON)

    if user_id in active_tasks:
        return await message.reply("❌ Pehle purana kaam khatam hone de ya `/cancel` kar.")

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Please reply to a `.zip` or `.rar` file!**")

    task = asyncio.create_task(unzip_logic(client, message))
    active_tasks[user_id] = task
    
    try:
        await task
    except asyncio.CancelledError:
        pass
    finally:
        if user_id in active_tasks:
            del active_tasks[user_id]

async def unzip_logic(client, message):
    user_id = message.from_user.id
    doc = message.reply_to_message.document
    if is_nsfw(doc.file_name):
        return await message.reply("🚫 **NSFW Blocked!** Archive name is restricted.")

    msg = await message.reply("⏳ **Downloading Archive... (Use /cancel to stop)**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading...")
    )
    
    extract_dir = f"{Config.DOWNLOAD_DIR}/extracted_{int(time.time())}"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        await msg.edit("⚙️ **Extracting... Please wait.**")
        if doc.file_name.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        else:
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)

        files_sent = 0
        for root, dirs, files in os.walk(extract_dir):
            for file_name in files:
                if asyncio.current_task().cancelled(): return

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
                except Exception: pass

        await msg.delete()
        if files_sent > 0:
            await message.reply(f"✅ **Done! Sent {files_sent} files.**")
            # ✅ Task successful, increment usage
            await db.increment_usage(user_id)
        else:
            await message.reply("❌ **No valid files found inside!**")

    except Exception as e:
        await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        shutil.rmtree(extract_dir, ignore_errors=True)


# --- ZIP HANDLER ---
@Client.on_message(filters.command("zip"))
async def zip_handler(client, message):
    user_id = message.from_user.id
    
    # 🚨 LIMIT CHECK
    if await is_limited(user_id):
        return await message.reply(LIMIT_TEXT, reply_markup=LIMIT_BUTTON)

    if user_id in active_tasks:
        return await message.reply("❌ Pehle purana kaam khatam hone de ya `/cancel` kar.")

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Please reply to any file with /zip**")

    task = asyncio.create_task(zip_logic(client, message))
    active_tasks[user_id] = task
    
    try:
        await task
    except asyncio.CancelledError:
        pass
    finally:
        if user_id in active_tasks:
            del active_tasks[user_id]

async def zip_logic(client, message):
    user_id = message.from_user.id
    doc = message.reply_to_message.document
    doc_name = doc.file_name or f"file_{int(time.time())}"
    
    if is_nsfw(doc_name):
        return await message.reply("🚫 **NSFW Blocked!**")

    if doc.file_size > 2000 * 1024 * 1024:
        return await message.reply("❌ **File is larger than 2GB.**")

    msg = await message.reply("⏳ **Downloading... (Use /cancel to stop)**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading...")
    )
    
    zip_path = f"{Config.DOWNLOAD_DIR}/{doc_name}.zip"

    try:
        if asyncio.current_task().cancelled(): return
        await msg.edit("⚙️ **Compressing...**")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, arcname=doc_name)

        start_time = time.time()
        sent_msg = await client.send_document(
            message.chat.id, zip_path,
            progress=progress_bar, progress_args=(msg, start_time, "Uploading ZIP...")
        )
        
        if Config.LOG_CHANNEL:
            await sent_msg.copy(Config.LOG_CHANNEL, caption=f"🗜️ Zipped by {message.from_user.id}")
            
        await msg.delete()
        await message.reply("✅ **ZIP Complete!**")
        # ✅ Increment usage
        await db.increment_usage(user_id)
    except Exception as e:
        await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(zip_path): os.remove(zip_path)
