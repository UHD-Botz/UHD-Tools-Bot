import os
import time
import zipfile
import rarfile
import shutil
from pyrogram import Client, filters
from config import Config

# Koyeb linux server me unrar command set karna zaroori hai rar files ke liye
rarfile.UNRAR_TOOL = "unrar"

@Client.on_message(filters.command("unzip"))
async def unzip_file(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Please reply to a `.zip` or `.rar` file with /unzip**")

    doc = message.reply_to_message.document
    if not doc.file_name.endswith(('.zip', '.rar')):
        return await message.reply("❌ **Only .zip and .rar files are supported!**")

    msg = await message.reply("⏳ **Downloading archive...**")
    file_path = await message.reply_to_message.download(file_name=f"{Config.DOWNLOAD_DIR}/")
    
    # Ek unique folder banayenge extraction ke liye taaki files mix na ho
    extract_dir = f"{Config.DOWNLOAD_DIR}/extracted_{int(time.time())}"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        await msg.edit("⏳ **Extracting files...**")
        
        # Zip aur Rar ka alag alag logic
        if doc.file_name.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif doc.file_name.endswith('.rar'):
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)

        extracted_files = os.listdir(extract_dir)
        if not extracted_files:
            return await msg.edit("❌ **Archive is empty or corrupted!**")

        await msg.edit(f"📤 **Uploading {len(extracted_files)} files...**")
        
        # Ek ek karke saari extracted files user ko bhejenge
        for file_name in extracted_files:
            full_path = os.path.join(extract_dir, file_name)
            if os.path.isfile(full_path):
                await client.send_document(message.chat.id, full_path)
        
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ **Error extracting file:** `{e}`")
    finally:
        # Server memory clean karne ke liye files remove karenge
        if os.path.exists(file_path): 
            os.remove(file_path)
        if os.path.exists(extract_dir): 
            shutil.rmtree(extract_dir)

@Client.on_message(filters.command("zip"))
async def zip_file(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Please reply to any file with /zip to compress it.**")

    msg = await message.reply("⏳ **Downloading file to compress...**")
    file_path = await message.reply_to_message.download(file_name=f"{Config.DOWNLOAD_DIR}/")
    
    doc_name = message.reply_to_message.document.file_name or f"file_{int(time.time())}"
    zip_path = f"{Config.DOWNLOAD_DIR}/{doc_name}.zip"

    try:
        await msg.edit("⏳ **Compressing into ZIP...**")
        
        # File ko high compression (ZIP_DEFLATED) ke sath zip karenge
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, arcname=doc_name)

        await msg.edit("📤 **Uploading ZIP file...**")
        await client.send_document(message.chat.id, zip_path)
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ **Error compressing file:** `{e}`")
    finally:
        # Server cleanup
        if os.path.exists(file_path): 
            os.remove(file_path)
        if os.path.exists(zip_path): 
            os.remove(zip_path)
