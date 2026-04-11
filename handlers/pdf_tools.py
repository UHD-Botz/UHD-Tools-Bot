import os
import time
from pyrogram import Client, filters
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from config import Config
from database.db import db
from utils.progress import progress_bar
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON

# --- PDF SPLIT (PAGE 1 EXTRACTION) ---
@Client.on_message(filters.command(["pdfsplit", "pdfspilt"]))
async def split_pdf(client, message):
    user_id = message.from_user.id
    
    # 🚨 LIMIT CHECK
    if await is_limited(user_id):
        return await message.reply(LIMIT_TEXT, reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Please reply to a PDF file with `/pdfsplit`**")
    
    doc = message.reply_to_message.document
    if not doc.file_name.lower().endswith('.pdf'):
        return await message.reply("❌ This is not a valid PDF file.")

    msg = await message.reply("⏳ **Downloading PDF...**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading PDF...")
    )
    
    out_path = f"{Config.DOWNLOAD_DIR}/split_{message.chat.id}.pdf"
    
    try:
        await msg.edit("⚙️ **Extracting Page 1...**")
        reader = PdfReader(file_path)
        
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except:
                return await msg.edit("❌ This PDF is Password Protected. Cannot read it.")

        writer = PdfWriter()
        writer.add_page(reader.pages[0])
            
        with open(out_path, "wb") as f:
            writer.write(f)
            
        start_time = time.time()
        sent_msg = await client.send_document(
            message.chat.id, 
            out_path, 
            caption="📑 **Successfully extracted Page 1.**",
            progress=progress_bar,
            progress_args=(msg, start_time, "Uploading Split PDF...")
        )
        
        if Config.LOG_CHANNEL:
            await sent_msg.copy(Config.LOG_CHANNEL, caption=f"📑 PDF Split by {user_id}")
            
        await msg.delete()
        # ✅ Increment usage
        await db.increment_usage(user_id)
        
    except Exception as e:
        await msg.edit(f"❌ **Error Splitting PDF:** `{str(e)}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)

# --- PDF TO IMAGES ---
@Client.on_message(filters.command("pdf2img"))
async def pdf_to_img(client, message):
    user_id = message.from_user.id
    
    # 🚨 LIMIT CHECK
    if await is_limited(user_id):
        return await message.reply(LIMIT_TEXT, reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ Reply to a PDF file with /pdf2img.")
    
    msg = await message.reply("⏳ **Converting PDF to Images (Max 5 pages)...**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading...")
    )
    
    try:
        # Convert first 5 pages
        images = convert_from_path(file_path, first_page=1, last_page=5)
        
        for i, image in enumerate(images):
            img_path = f"{Config.DOWNLOAD_DIR}/page_{i}.jpg"
            image.save(img_path, 'JPEG')
            await client.send_photo(message.chat.id, img_path, caption=f"Page {i+1}")
            os.remove(img_path)
            
        await msg.delete()
        await message.reply("✅ **Successfully converted first 5 pages!**")
        # ✅ Increment usage
        await db.increment_usage(user_id)
        
    except Exception as e:
        await msg.edit(f"❌ Error: Ensure poppler is installed on server.\n`{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
