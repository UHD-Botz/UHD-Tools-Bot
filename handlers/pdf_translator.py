import os
import time
import asyncio
from pyrogram import Client, filters
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
from config import Config
from database.db import db
from utils.progress import progress_bar
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON, FSUB_TEXT, FSUB_BUTTON

@Client.on_message(filters.command(["pdfsplit", "pdfspilt"]))
async def split_pdf(client, message):
    user_id = message.from_user.id
    
    status = await is_limited(user_id, "pdfsplit", client)
    if status == "FSUB_REQUIRED":
        return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True:
        return await message.reply(LIMIT_TEXT.format(cmd="pdfsplit"), reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Reply to a PDF file with `/pdfsplit`**")
    
    msg = await message.reply("⏳ **Processing...**")
    start_time = time.time()
    
    try:
        file_path = await message.reply_to_message.download(
            file_name=f"{Config.DOWNLOAD_DIR}/sp_{user_id}.pdf",
            progress=progress_bar, progress_args=(msg, start_time, "Downloading...")
        )
        
        await asyncio.sleep(2)
        out_path = f"{Config.DOWNLOAD_DIR}/final_{user_id}.pdf"
        
        reader = PdfReader(file_path)
        writer = PdfWriter()
        writer.add_page(reader.pages[0])
        
        with open(out_path, "wb") as f:
            writer.write(f)
            
        await msg.edit("📤 **Uploading...**")
        await client.send_document(message.chat.id, out_path, caption="📑 **Page 1 Extracted Successfully!**\n\n🛡️ @UHDBots")
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
    status = await is_limited(user_id, "pdf2img", client)
    if status == "FSUB_REQUIRED":
        return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True:
        return await message.reply(LIMIT_TEXT.format(cmd="pdf2img"), reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message:
        return await message.reply("⚠️ Reply to a PDF with /pdf2img.")
    
    msg = await message.reply("⏳ **Converting to Images...**")
    start_time = time.time()
    file_path = await message.reply_to_message.download(progress=progress_bar, progress_args=(msg, start_time, "Downloading..."))
    
    await asyncio.sleep(2)
    try:
        images = convert_from_path(file_path, first_page=1, last_page=5)
        for i, image in enumerate(images):
            img_path = f"{Config.DOWNLOAD_DIR}/p_{i}_{user_id}.jpg"
            draw = ImageDraw.Draw(image)
            w, h = image.size
            font_size = int(h / 15)
            try: font = ImageFont.truetype("arial.ttf", font_size)
            except: font = ImageFont.load_default()
            
            draw.text((w - (font_size * 5), h - (font_size * 2)), "@UHDBots", fill=(128, 128, 128), font=font)
            image.save(img_path, 'JPEG')
            await client.send_photo(message.chat.id, img_path, caption=f"Page {i+1} | @UHDBots")
            os.remove(img_path)
            
        await msg.delete()
        await db.increment_usage(user_id, "pdf2img")
    except Exception as e: await msg.edit(f"❌ Error: {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
