import os
from pyrogram import Client, filters
from PyPDF2 import PdfReader
from fpdf import FPDF
from deep_translator import GoogleTranslator
from config import Config

@Client.on_message(filters.command("pdftranslate"))
async def translate_pdf(client, message):
    if len(message.command) < 2 or not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply("Reply to a PDF with `/pdftranslate <language_code>`\nExample: `/pdftranslate hi` for Hindi")

    lang_code = message.command[1]
    msg = await message.reply("⏳ Downloading and Extracting text...")
    file_path = await message.reply_to_message.download(file_name=f"{Config.DOWNLOAD_DIR}/")
    out_path = f"{Config.DOWNLOAD_DIR}/translated_{message.chat.id}.pdf"

    try:
        reader = PdfReader(file_path)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12) # Note: FPDF supports limited fonts by default.
        
        translator = GoogleTranslator(source='auto', target=lang_code)
        
        for i, page in enumerate(reader.pages):
            await msg.edit(f"⏳ Translating page {i+1}/{len(reader.pages)}...")
            text = page.extract_text()
            if text:
                # Chunking text for translation limits
                chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                for chunk in chunks:
                    translated = translator.translate(chunk)
                    # Use latin-1 encode/decode to avoid FPDF character errors for basic setup
                    clean_text = translated.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 10, clean_text)
                    
        pdf.output(out_path)
        await msg.edit("📤 Uploading Translated PDF...")
        await client.send_document(message.chat.id, out_path, caption=f"Translated to {lang_code.upper()}")
    except Exception as e:
        await msg.edit(f"❌ Translation Error: {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)
