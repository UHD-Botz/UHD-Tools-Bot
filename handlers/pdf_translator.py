import os
from pyrogram import Client, filters
from PyPDF2 import PdfReader
from fpdf import FPDF
from deep_translator import GoogleTranslator
from config import Config

# Language Code Mapper Fix
LANG_MAP = {"hindi": "hi", "english": "en", "spanish": "es", "french": "fr", "bengali": "bn", "urdu": "ur"}

@Client.on_message(filters.command("pdftranslate"))
async def translate_pdf(client, message):
    if len(message.command) < 2 or not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("Reply to a PDF with `/pdftranslate hindi` or `/pdftranslate hi`")

    # Smart detection: Convert "hindi" to "hi"
    user_lang = message.command[1].lower()
    lang_code = LANG_MAP.get(user_lang, user_lang)

    msg = await message.reply("⏳ Downloading PDF...")
    file_path = await message.reply_to_message.download(file_name=f"{Config.DOWNLOAD_DIR}/")
    out_path = f"{Config.DOWNLOAD_DIR}/translated_{message.chat.id}.pdf"

    try:
        reader = PdfReader(file_path)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        translator = GoogleTranslator(source='auto', target=lang_code)
        
        for i, page in enumerate(reader.pages):
            await msg.edit(f"⏳ Translating page {i+1}...")
            text = page.extract_text()
            if text:
                chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                for chunk in chunks:
                    translated = translator.translate(chunk)
                    clean_text = translated.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 10, clean_text)
                    
        pdf.output(out_path)
        await msg.edit("📤 Uploading Translated PDF...")
        await client.send_document(message.chat.id, out_path)
    except Exception as e:
        await msg.edit(f"❌ Translation Error: Make sure language code is correct. Details: `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)
