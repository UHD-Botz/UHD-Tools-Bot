import os
import time
import asyncio
from pyrogram import Client, filters
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont # <-- Sabse zaroori
from config import Config
from database.db import db
from utils.progress import progress_bar
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON

# --- PDF TO IMAGES (BIG WATERMARK) ---
@Client.on_message(filters.command("pdf2img"))
async def pdf_to_img(client, message):
    user_id = message.from_user.id
    if await is_limited(user_id, "pdf2img"):
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
            font_size = int(h / 20) # Image ki height ka 5% size
            try:
                # Agar server pe font file hai toh use karo, warna default
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

            # Bottom-Right Position with padding
            text = "@UHDBots"
            draw.text((w - (font_size * 5), h - (font_size * 2)), text, fill=(128, 128, 128), font=font)
            
            image.save(img_path, 'JPEG')
            await client.send_photo(message.chat.id, img_path, caption=f"Page {i+1} | @UHDBots")
            os.remove(img_path)
            
        await msg.delete()
        await db.increment_usage(user_id, "pdf2img")
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

# --- WRITE COMMAND (TEXT TO HANDWRITTEN) ---
@Client.on_message(filters.command("write"))
async def write_text(client, message):
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        return await message.reply("⚠️ Usage: `/write Tera message yahan likho`")

    # Limit check for "write"
    if await is_limited(user_id, "write"):
        return await message.reply(LIMIT_TEXT.format(cmd="write"), reply_markup=LIMIT_BUTTON)

    text = message.text.split(None, 1)[1]
    msg = await message.reply("📝 **Writing on paper...**")
    
    img_path = f"{Config.DOWNLOAD_DIR}/write_{user_id}.jpg"
    
    try:
        # Ek white page create karo (A4 size approx)
        img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw lines like a notebook
        for y in range(50, 1000, 40):
            draw.line([(0, y), (800, y)], fill=(200, 200, 255), width=1)
            
        # Write the text
        draw.text((50, 60), text, fill=(0, 0, 150)) # Blue ink
        
        # 🔥 BIG WATERMARK ON WRITTEN PAGE
        draw.text((600, 950), "@UHDBots", fill=(200, 200, 200))

        img.save(img_path)
        await client.send_photo(message.chat.id, img_path, caption="✍️ **Your Handwritten Note**\n\n🛡️ @UHDBots")
        await msg.delete()
        os.remove(img_path)
        
        await db.increment_usage(user_id, "write")
        
    except Exception as e:
        await msg.edit(f"❌ Error in Writing: {e}")
