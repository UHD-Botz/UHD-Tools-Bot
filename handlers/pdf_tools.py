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

# --- PDF SPLIT (PAGE 1 EXTRACTION) ---
@Client.on_message(filters.command(["pdfsplit", "pdfspilt"]))
async def split_pdf(client, message):
    user_id = message.from_user.id
    
    # 🔍 Force Peer Recognition (Fix for PEER_ID_INVALID)
    try:
        await client.get_chat(Config.FORCE_SUB_CHANNEL)
    except:
        pass

    # 🚨 FSUB & LIMIT CHECK
    status = await is_limited(user_id, "pdfsplit", client)
    if status == "FSUB_REQUIRED":
        return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True:
        return await message.reply(LIMIT_TEXT.format(cmd="pdfsplit"), reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ **Please reply to a PDF file with `/pdfsplit`**")
    
    msg = await message.reply("⏳ **Processing PDF...**")
    start_time = time.time()
    
    try:
        file_path = await message.reply_to_message.download(
            file_name=f"{Config.DOWNLOAD_DIR}/split_{user_id}.pdf",
            progress=progress_bar,
            progress_args=(msg, start_time, "Downloading...")
        )
        
        await asyncio.sleep(2) # Safety gap for disk write
        out_path = f"{Config.DOWNLOAD_DIR}/final_split_{user_id}.pdf"
        
        reader = PdfReader(file_path)
        writer = PdfWriter()
        writer.add_page(reader.pages[0])
        
        with open(out_path, "wb") as f:
            writer.write(f)
            
        await msg.edit("📤 **Uploading...**")
        sent_msg = await client.send_document(
            message.chat.id, 
            out_path, 
            caption="📑 **Page 1 Extracted Successfully!**\n\n🛡️ @UHDBots",
        )
        
        if Config.LOG_CHANNEL:
            await sent_msg.copy(Config.LOG_CHANNEL, caption=f"📑 Split by {user_id}")

        await msg.delete()
        await db.increment_usage(user_id, "pdfsplit")
        
    except Exception as e:
        await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if 'file_path' in locals() and os.path.exists(file_path): os.remove(file_path)
        if 'out_path' in locals() and os.path.exists(out_path): os.remove(out_path)

# --- PDF TO IMAGES (BIG WATERMARK) ---
@Client.on_message(filters.command("pdf2img"))
async def pdf_to_img(client, message):
    user_id = message.from_user.id
    
    status = await is_limited(user_id, "pdf2img", client)
    if status == "FSUB_REQUIRED":
        return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True:
        return await message.reply(LIMIT_TEXT.format(cmd="pdf2img"), reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ Reply to a PDF with /pdf2img.")
    
    msg = await message.reply("⏳ **Converting & Watermarking...**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/img_{user_id}.pdf",
        progress=progress_bar, progress_args=(msg, start_time, "Downloading...")
    )
    
    await asyncio.sleep(2)

    try:
        images = convert_from_path(file_path, first_page=1, last_page=5)
        for i, image in enumerate(images):
            img_path = f"{Config.DOWNLOAD_DIR}/page_{i}_{user_id}.jpg"
            
            draw = ImageDraw.Draw(image)
            w, h = image.size
            
            # 🔥 BIG WATERMARK (FontSize scaled to Image Height)
            font_size = int(h / 15) # Watermark size increased
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

            text = "@UHDBots"
            # Draw with grey color and transparency feel
            draw.text((w - (font_size * 5), h - (font_size * 2)), text, fill=(128, 128, 128), font=font)
            
            image.save(img_path, 'JPEG')
            await client.send_photo(message.chat.id, img_path, caption=f"Page {i+1} | @UHDBots")
            os.remove(img_path)
            
        await msg.delete()
        await db.increment_usage(user_id, "pdf2img")
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")
    finally:
        if 'file_path' in locals() and os.path.exists(file_path): os.remove(file_path)

# --- WRITE COMMAND (TEXT TO HANDWRITTEN) ---
@Client.on_message(filters.command("write"))
async def write_text(client, message):
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        return await message.reply("⚠️ Usage: `/write Tera message yahan likho`")

    status = await is_limited(user_id, "write", client)
    if status == "FSUB_REQUIRED":
        return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True:
        return await message.reply(LIMIT_TEXT.format(cmd="write"), reply_markup=LIMIT_BUTTON)

    text = message.text.split(None, 1)[1]
    msg = await message.reply("📝 **Writing on paper...**")
    
    img_path = f"{Config.DOWNLOAD_DIR}/write_{user_id}.jpg"
    
    try:
        # Notebook Page Simulation
        img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Notebook Lines
        for y in range(50, 1000, 40):
            draw.line([(0, y), (800, y)], fill=(200, 200, 255), width=1)
            
        # Draw Text
        draw.text((50, 60), text, fill=(0, 0, 150)) # Blue ink
        
        # Branding Watermark
        draw.text((600, 950), "@UHDBots", fill=(200, 200, 200))

        img.save(img_path)
        await client.send_photo(message.chat.id, img_path, caption="✍️ **Your Handwritten Note**\n\n🛡️ @UHDBots")
        await msg.delete()
        
        await db.increment_usage(user_id, "write")
        
    except Exception as e:
        await msg.edit(f"❌ Error in Writing: {e}")
    finally:
        if os.path.exists(img_path): os.remove(img_path)
