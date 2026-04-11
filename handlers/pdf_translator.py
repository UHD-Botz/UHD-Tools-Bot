import os
import time
import asyncio
from pyrogram import Client, filters
from PyPDF2 import PdfReader
from fpdf import FPDF
from deep_translator import GoogleTranslator
from config import Config
from database.db import db
from utils.progress import progress_bar
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON

LANG_MAP = {"hindi": "hi", "english": "en", "spanish": "es", "french": "fr", "bengali": "bn", "urdu": "ur"}

@Client.on_message(filters.command("pdftranslate"))
async def translate_pdf(client, message):
    user_id = message.from_user.id
    
    if await is_limited(user_id, "pdftranslate"):
        return await message.reply(LIMIT_TEXT.format(cmd="pdftranslate"), reply_markup=LIMIT_BUTTON)

    if len(message.command) < 2 or not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("⚠️ Reply to a PDF with `/pdftranslate hindi` or `/pdftranslate hi`")

    user_lang = message.command[1].lower()
    lang_code = LANG_MAP.get(user_lang, user_lang)

    msg = await message.reply("⏳ **Downloading PDF for Translation...**")
    start_time = time.time()
    
    file_path = await message.reply_to_message.download(
        file_name=f"{Config.DOWNLOAD_DIR}/",
        progress=progress_bar,
        progress_args=(msg, start_time, "Downloading PDF...")
    )
    
    # ⏱️ Wait for file to settle
    await asyncio.sleep(2)
    
    out_path = f"{Config.DOWNLOAD_DIR}/translated_{message.chat.id}.pdf"

    try:
        reader = PdfReader(file_path)
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        translator = GoogleTranslator(source='auto', target=lang_code)
        pages_to_translate = min(len(reader.pages), 3)

        for i in range(pages_to_translate):
            await msg.edit(f"⏳ **Translating page {i+1} of {pages_to_translate}...**")
            pdf.add_page()
            
            # 🏷️ WATERMARK (Bottom-Right)
            pdf.set_font("Arial", 'I', 8)
            pdf.set_text_color(128, 128, 128)
            pdf.text(170, 290, "@UHDBots") # Position adjusted for A4
            
            pdf.set_font("Arial", size=11)
            pdf.set_text_color(0, 0, 0)
            
            text = reader.pages[i].extract_text()
            if text:
                chunks = [text[j:j+4000] for j in range(0, len(text), 4000)]
                for chunk in chunks:
                    translated = translator.translate(chunk)
                    clean_text = translated.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 8, clean_text)
                    
        pdf.output(out_path)
        
        await msg.edit("📤 **Uploading Translated PDF...**")
        sent_msg = await client.send_document(
            message.chat.id, 
            out_path,
            caption=f"✅ **Translated to {lang_code.upper()}**\n\n🛡️ Watermarked: @UHDBots",
        )
        
        if Config.LOG_CHANNEL:
            await sent_msg.copy(Config.LOG_CHANNEL, caption=f"🌐 Translated by {user_id}")

        await msg.delete()
        await db.increment_usage(user_id, "pdftranslate")

    except Exception as e:
        await msg.edit(f"❌ **Translation Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)
