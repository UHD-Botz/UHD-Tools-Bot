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

# Important for RAR support on some servers
rarfile.UNRAR_TOOL = "unrar"

# Task Management
active_tasks = {}

@Client.on_message(filters.command("cancel"))
async def cancel_task(client, message):
    user_id = message.from_user.id
    if user_id in active_tasks:
        active_tasks[user_id].cancel()
        # del active_tasks[user_id] -> finally block handles this
        await message.reply("⛔ **Process Cancelled Successfully!**")
    else:
        await message.reply("⚠️ Tera koi active process nahi chal raha hai.")

# --- UNZIP HANDLER ---
@Client.on_message(filters.command("unzip"))
async def unzip_handler(client, message):
    user_id = message.from_user.id
    
    # 🚨 FSUB & LIMIT CHECK
    # Note: Passing client for potential Peer Recognition
    if await is_limited(user_id, "unzip"):
        return await message.reply(LIMIT_TEXT.format(cmd="unzip"), reply_markup=LIMIT_BUTTON)

    if user_id in active_tasks:
        return await message.reply("❌ Pehle purana kaam khatam hone de ya `/cancel` kar.")

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Please reply to a `.zip` or `.rar` file!**")

    # Start Task
    task = asyncio.create_task(unzip_logic(client, message))
    active_tasks[user_id] = task
    
    try:
        await task
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Task Error: {e}")
    finally:
        active_tasks.pop(user_id, None)

async def unzip_logic(client, message):
    user_id = message.from_user.id
    doc = message.reply_to_message.document
    
    if is_nsfw(doc.file_name):
        return await message.reply("🚫 **NSFW Blocked!** Archive name is restricted.")

    msg = await message.reply("⏳ **Downloading Archive... (Use /cancel to stop)**")
    start_time = time.time()
    
    # Unique naming to prevent file overlap
    unique_id = int(time.time())
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/unzip_{user_id}_{unique_id}.zip",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading...")
    )
    
    extract_dir = f"{Config.DOWNLOAD_DIR}/extracted_{user_id}_{unique_id}"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        await msg.edit("⚙️ **Extracting... Please wait.**")
        # Support for ZIP and RAR
        if doc.file_name.lower().endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        else:
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)

        files_sent = 0
        for root, dirs, files in os.walk(extract_dir):
            for file_name in files:
                # Check cancellation at every file step
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
                        caption=f"📄 `{file_name}`\n\n🛡️ @UHDBots",
                        progress=progress_bar,
                        progress_args=(msg, start_time, f"Uploading: {file_name}")
                    )
                    files_sent += 1
                    if Config.LOG_CHANNEL:
                        await sent_msg.copy(Config.LOG_CHANNEL, caption=f"👤 By: {user_id}")
                except Exception:
                    continue

        await msg.delete()
        if files_sent > 0:
            await message.reply(f"✅ **Done! Sent {files_sent} files.**")
            await db.increment_usage(user_id, "unzip")
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
    
    if await is_limited(user_id, "zip"):
        return await message.reply(LIMIT_TEXT.format(cmd="zip"), reply_markup=LIMIT_BUTTON)

    if user_id in active_tasks:
        return await message.reply("❌ Pehle purana kaam khatam hone de ya `/cancel` kar.")

    if not message.reply_to_message:
        return await message.reply("⚠️ **Please reply to any file with /zip**")

    task = asyncio.create_task(zip_logic(client, message))
    active_tasks[user_id] = task
    
    try:
        await task
    except asyncio.CancelledError:
        pass
    finally:
        active_tasks.pop(user_id, None)

async def zip_logic(client, message):
    user_id = message.from_user.id
    reply = message.reply_to_message
    
    # Can be document, video, or photo
    doc = reply.document or reply.video or reply.audio
    doc_name = getattr(doc, 'file_name', f"file_{int(time.time())}")
    
    if is_nsfw(doc_name):
        return await message.reply("🚫 **NSFW Blocked!**")

    if doc and doc.file_size > 2000 * 1024 * 1024:
        return await message.reply("❌ **File is larger than 2GB.**")

    msg = await message.reply("⏳ **Downloading... (Use /cancel to stop)**")
    start_time = time.time()
    
    unique_id = int(time.time())
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/zip_{user_id}_{unique_id}",
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
            message.chat.id, 
            zip_path,
            caption=f"🗜️ **ZIP Archive Created**\n\n🛡️ @UHDBots",
            progress=progress_bar, 
            progress_args=(msg, start_time, "Uploading ZIP...")
        )
        
        if Config.LOG_CHANNEL:
            await sent_msg.copy(Config.LOG_CHANNEL, caption=f"🗜️ Zipped by {user_id}")
            
        await msg.delete()
        await message.reply("✅ **ZIP Complete!**")
        await db.increment_usage(user_id, "zip")
        
    except Exception as e:
        await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(zip_path): os.remove(zip_path)
