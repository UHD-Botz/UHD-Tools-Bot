import os
import time
import asyncio
from pyrogram import Client, filters
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path
from config import Config
from database.db import db
from utils.progress import progress_bar
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON

# --- PDF SPLIT UPDATE ---
@Client.on_message(filters.command(["pdfsplit", "pdfspilt"]))
async def split_pdf(client, message):
    user_id = message.from_user.id
    if await is_limited(user_id, "pdfsplit"):
        return await message.reply(LIMIT_TEXT.format(cmd="pdfsplit"), reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ Reply to a PDF with `/pdfsplit`")
    
    msg = await message.reply("⏳ **Processing PDF...**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/pdf_split_{user_id}.pdf",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading...")
    )
    
    await asyncio.sleep(1) # Safety gap
    out_path = f"{Config.DOWNLOAD_DIR}/split_final_{user_id}.pdf"
    
    try:
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        page = reader.pages[0]
        writer.add_page(page)
        
        # 🏷️ Watermark adding logic can be complex in split, 
        # but Caption is the best place for username
        
        with open(out_path, "wb") as f:
            writer.write(f)
            
        await msg.edit("📤 **Uploading...**")
        sent_msg = await client.send_document(
            message.chat.id, 
            out_path, 
            caption="📑 **Successfully extracted Page 1.**\n\n🛡️ Powered By: @UHDBots",
        )
        
        await msg.delete()
        await db.increment_usage(user_id, "pdfsplit")
        
    except Exception as e:
        await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)

@Client.on_message(filters.command("pdf2img"))
async def pdf_to_img(client, message):
    user_id = message.from_user.id
    if await is_limited(user_id, "pdf2img"):
        return await message.reply(LIMIT_TEXT.format(cmd="pdf2img"), reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ Reply to a PDF file with /pdf2img.")
    
    msg = await message.reply("⏳ **Converting PDF to Images...**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/pdf_img_{user_id}.pdf",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading...")
    )
    
    await asyncio.sleep(2) # Fix for "Ruka hua" issue

    try:
        images = convert_from_path(file_path, first_page=1, last_page=5)
        
        for i, image in enumerate(images):
            img_path = f"{Config.DOWNLOAD_DIR}/page_{i}_{user_id}.jpg"
            
            # 🏷️ IMAGE WATERMARK LOGIC
            draw = ImageDraw.Draw(image)
            # Yahan hum text likh rahe hain (Position: Bottom-Right)
            # Width aur Height ke hisaab se adjust
            width, height = image.size
            text = "@UHDBots"
            
            # Drawing a small semi-transparent rectangle or just text
            draw.text((width - 150, height - 50), text, fill=(128, 128, 128)) 
            
            image.save(img_path, 'JPEG')
            await client.send_photo(message.chat.id, img_path, caption=f"Page {i+1} | @UHDBots")
            os.remove(img_path)
            
        await msg.delete()
        await db.increment_usage(user_id, "pdf2img")
        
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
