import os
import time
import asyncio
import fitz  # PyMuPDF for fast text extraction
from pyrogram import Client, filters
from PyPDF2 import PdfReader, PdfWriter
from config import Config
from database.db import db
from utils.progress import progress_bar
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON, FSUB_TEXT, FSUB_BUTTON

@Client.on_message(filters.command("pdftext"))
async def extract_text(client, message):
    user_id = message.from_user.id
    status = await is_limited(user_id, "pdftext", client)
    if status == "FSUB_REQUIRED": return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True: return await message.reply(LIMIT_TEXT.format(cmd="pdftext"), reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Reply to a PDF file with `/pdftext`**")

    msg = await message.reply("⏳ **Extracting Text...**")
    file_path = await message.reply_to_message.download()
    await asyncio.sleep(1)

    try:
        doc = fitz.open(file_path)
        text = ""
        # Sirf pehle 5 pages extract karenge free users ke liye (ya server bachane ke liye)
        for i in range(min(len(doc), 5)):
            text += f"--- Page {i+1} ---\n{doc[i].get_text()}\n\n"
            
        if not text.strip():
            return await msg.edit("❌ **No text found! (Image based PDF?)**")

        # Agar text lamba hai toh file bhej do, warna message
        if len(text) > 3000:
            out_path = f"{Config.DOWNLOAD_DIR}/text_{user_id}.txt"
            with open(out_path, "w", encoding="utf-8") as f: f.write(text)
            await client.send_document(message.chat.id, out_path, caption="📄 **Extracted Text**\n\n🛡️ @UHDBots")
            os.remove(out_path)
            await msg.delete()
        else:
            await msg.edit(f"📄 **Extracted Text:**\n\n`{text}`\n\n🛡️ @UHDBots")
            
        await db.increment_usage(user_id, "pdftext")
    except Exception as e: await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

@Client.on_message(filters.command("pdflock"))
async def lock_pdf(client, message):
    user_id = message.from_user.id
    status = await is_limited(user_id, "pdflock", client)
    if status == "FSUB_REQUIRED": return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True: return await message.reply(LIMIT_TEXT.format(cmd="pdflock"), reply_markup=LIMIT_BUTTON)

    if len(message.command) < 2 or not message.reply_to_message:
        return await message.reply("⚠️ **Usage:** Reply to PDF with `/pdflock password`")

    password = message.command[1]
    msg = await message.reply("🔒 **Locking PDF...**")
    file_path = await message.reply_to_message.download()
    out_path = f"{Config.DOWNLOAD_DIR}/locked_{user_id}.pdf"
    
    try:
        reader = PdfReader(file_path)
        writer = PdfWriter()
        for page in reader.pages: writer.add_page(page)
        
        writer.encrypt(password)
        with open(out_path, "wb") as f: writer.write(f)
            
        await client.send_document(message.chat.id, out_path, caption=f"🔐 **PDF Locked!**\nPassword: ||{password}||\n\n🛡️ @UHDBots")
        await msg.delete()
        await db.increment_usage(user_id, "pdflock")
    except Exception as e: await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)

@Client.on_message(filters.command("pdfunlock"))
async def unlock_pdf(client, message):
    user_id = message.from_user.id
    status = await is_limited(user_id, "pdfunlock", client)
    if status == "FSUB_REQUIRED": return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True: return await message.reply(LIMIT_TEXT.format(cmd="pdfunlock"), reply_markup=LIMIT_BUTTON)

    if len(message.command) < 2 or not message.reply_to_message:
        return await message.reply("⚠️ **Usage:** Reply to Locked PDF with `/pdfunlock password`")

    password = message.command[1]
    msg = await message.reply("🔓 **Unlocking PDF...**")
    file_path = await message.reply_to_message.download()
    out_path = f"{Config.DOWNLOAD_DIR}/unlocked_{user_id}.pdf"
    
    try:
        reader = PdfReader(file_path)
        if reader.is_encrypted:
            reader.decrypt(password)
            writer = PdfWriter()
            for page in reader.pages: writer.add_page(page)
            with open(out_path, "wb") as f: writer.write(f)
            await client.send_document(message.chat.id, out_path, caption="🔓 **PDF Unlocked!**\n\n🛡️ @UHDBots")
            await msg.delete()
            await db.increment_usage(user_id, "pdfunlock")
        else:
            await msg.edit("⚠️ **This PDF is not locked.**")
    except Exception as e: await msg.edit(f"❌ **Wrong Password or Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)
