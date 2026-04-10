from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from keep_alive import keep_alive
from database.db import db
import os

app = Client(
    "UHDToolsBot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    plugins=dict(root="handlers") # Automatically loads all files in handlers folder!
)

@app.on_message(filters.command("start"))
async def start(client, message):
    user = message.from_user
    is_new = await db.add_user(user.id, user.first_name)
    
    if is_new:
        await client.send_message(Config.LOG_CHANNEL, f"🚨 New User: {user.mention} (`{user.id}`)")
        
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 PDF Tools", callback_data="help_pdf"),
         InlineKeyboardButton("🛠️ Misc Tools", callback_data="help_misc")]
    ])
    
    await message.reply(
        f"👋 Hello {user.mention}!\n\n"
        "Welcome to **UHD Tools Bot**. I am your all-in-one free utility bot.\n"
        "Choose a category below to see available commands:",
        reply_markup=buttons
    )

@app.on_callback_query(filters.regex("help_pdf"))
async def help_pdf(client, callback_query):
    await callback_query.message.edit_text(
        "📄 **PDF TOOLS**\n"
        "/pdfsplit - Split a PDF (reply to file)\n"
        "/pdf2img - Convert PDF to Images\n"
        "/pdftranslate <lang> - Translate PDF to any language (reply to file)"
    )

@app.on_callback_query(filters.regex("help_misc"))
async def help_misc(client, callback_query):
    await callback_query.message.edit_text(
        "🛠️ **MISC TOOLS**\n"
        "/tempmail - Get fake email\n"
        "/inbox <email> - Check emails\n"
        "/quiz - Play Math Quiz\n"
        "/write <topic> - Auto write assignment paragraph"
    )

if __name__ == "__main__":
    print("Starting Keep Alive Server...")
    keep_alive()
    print("Bot is Starting...")
    app.run()
