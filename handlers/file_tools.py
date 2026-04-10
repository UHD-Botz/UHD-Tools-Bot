import os
import time
import zipfile
import rarfile
import shutil
from pyrogram import Client, filters
from config import Config
from utils.progress import progress_bar # <-- Progress bar import kiya

rarfile.UNRAR_TOOL = "unrar"

@Client.on_message(filters.command("unzip"))
async def unzip_file(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Please reply to a `.zip` or `.rar` file with /unzip**")

    doc = message.reply_to_message.document
    if not doc.file_name.endswith(('.zip', '.rar')):
        return await message.reply("❌ **Only .zip and .rar files are supported!**")

    # 2GB Limit Check
    if doc.file_size > 2000 * 1024 * 1024:
        return await message.reply("❌ **File is larger than 2GB. Telegram bots cannot download files larger than 2GB!**")

    msg = await message.reply("⏳ **Preparing to Download...**")
    start_time = time.time()
    
    # Downloading with Live Progress
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading Archive...")
    )
    
    extract_dir = f"{Config.DOWNLOAD_DIR}/extracted_{int(time.time())}"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        await msg.edit("⚙️ **Extracting files... Please wait!**") # Extraction CPU bound hota hai, isliye wahan percentage nahi hota
        
        if doc.file_name.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif doc.file_name.endswith('.rar'):
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)

        extracted_files = os.listdir(extract_dir)
        if not extracted_files:
            return await msg.edit("❌ **Archive is empty or corrupted!**")
        
        # Uploading with Live Progress
        for file_name in extracted_files:
            full_path = os.path.join(extract_dir, file_name)
            if os.path.isfile(full_path):
                start_time = time.time() # Har file ke liye naya time
                await client.send_document(
                    message.chat.id, 
                    full_path,
                    progress=progress_bar,
                    progress_args=(msg, start_time, f"Uploading: {file_name}")
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
    if doc.file_size > 2000 * 1024 * 1024:
        return await message.reply("❌ **File is larger than 2GB (Telegram limit).**")

    msg = await message.reply("⏳ **Preparing to Download...**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading File to Compress...")
    )
    
    doc_name = doc.file_name or f"file_{int(time.time())}"
    zip_path = f"{Config.DOWNLOAD_DIR}/{doc_name}.zip"

    try:
        await msg.edit("⚙️ **Compressing into ZIP... Please wait!**")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, arcname=doc_name)

        start_time = time.time()
        await client.send_document(
            message.chat.id, 
            zip_path,
            progress=progress_bar,
            progress_args=(msg, start_time, "Uploading Compressed ZIP...")
        )
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ **Error compressing file:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(zip_path): os.remove(zip_path)
