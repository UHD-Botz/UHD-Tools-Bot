import os
from pyrogram import Client, filters
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from config import Config

@Client.on_message(filters.command("pdfsplit"))
async def split_pdf(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("Reply to a PDF file with /pdfsplit to extract pages.")
    
    doc = message.reply_to_message.document
    if not doc.file_name.lower().endswith('.pdf'):
        return await message.reply("❌ This is not a valid PDF file.")

    msg = await message.reply("⏳ Downloading PDF...")
    file_path = await message.reply_to_message.download(file_name=f"{Config.DOWNLOAD_DIR}/")
    out_path = f"{Config.DOWNLOAD_DIR}/split_{message.chat.id}.pdf"
    
    try:
        reader = PdfReader(file_path)
        
        # Agar PDF lock hai par blank password hai, toh decrypt karo
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except:
                return await msg.edit("❌ This PDF is Password Protected. Cannot split.")

        writer = PdfWriter()
        total_pages = len(reader.pages)
        
        # Extract first 2 pages (ya jitne bhi hain agar 2 se kam hain)
        pages_to_extract = min(2, total_pages)
        for i in range(pages_to_extract):
            writer.add_page(reader.pages[i])
            
        with open(out_path, "wb") as f:
            writer.write(f)
            
        await msg.edit("📤 Uploading split PDF...")
        await client.send_document(message.chat.id, out_path, caption=f"📑 Extracted {pages_to_extract} page(s) out of {total_pages}.")
    except Exception as e:
        await msg.edit(f"❌ **PDF Split Error:** `{e}`\n\n(File might be corrupted or unsupported format).")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)


@Client.on_message(filters.command("pdf2img"))
async def pdf_to_img(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("Reply to a PDF file with /pdf2img.")
    
    msg = await message.reply("⏳ Converting PDF to Images (Max 5 pages)...")
    file_path = await message.reply_to_message.download(file_name=f"{Config.DOWNLOAD_DIR}/")
    
    try:
        images = convert_from_path(file_path, first_page=1, last_page=5)
        for i, image in enumerate(images):
            img_path = f"{Config.DOWNLOAD_DIR}/page_{i}.jpg"
            image.save(img_path, 'JPEG')
            await client.send_photo(message.chat.id, img_path)
            os.remove(img_path)
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ Error: Ensure poppler is installed. {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
