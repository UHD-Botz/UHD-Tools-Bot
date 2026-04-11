import asyncio
import uvloop
import os
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, PeerIdInvalid
from config import Config
from keep_alive import keep_alive
from database.db import db


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

app = Client(
    "UHDToolsBot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    plugins=dict(root="handlers"),
    sleep_threshold=120
)

Config.BOT_START_TIME = time.time()

# --- FORCE SUB CHECKER (PEER ID FIXED) ---
async def check_fsub(client, message):
    if not Config.FORCE_SUB_CHANNEL:
        return True 
    
    try:
        # 🛡️ PEER ID FIX: Pehle channel ko fetch karo
        try:
            await client.get_chat(Config.FORCE_SUB_CHANNEL)
        except PeerIdInvalid:
            pass # Agar invalid ho toh ignore karke member check pe jao
            
        await client.get_chat_member(Config.FORCE_SUB_CHANNEL, message.from_user.id)
        return True
    except UserNotParticipant:
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("📢 ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ", url=Config.FORCE_SUB_LINK)]])
        await message.reply("⚠️ **ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴏғғɪᴄɪᴀʟ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ!**", reply_markup=btn)
        return False
    except Exception as e:
        print(f"FSub Error: {e}")
        return True

# --- MAIN MENU TEXT & BUTTONS ---
def get_main_menu():
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 PDF Tools", callback_data="help_pdf"),
         InlineKeyboardButton("🎥 Video Tools", callback_data="help_video")],
        [InlineKeyboardButton("🔐 Security", callback_data="help_sec"),
         InlineKeyboardButton("🖼️ Image Tools", callback_data="help_img")],
        [InlineKeyboardButton("🗜️ Zip/Files", callback_data="help_file"),
         InlineKeyboardButton("🛠️ Misc Tools", callback_data="help_misc")],
        [InlineKeyboardButton("💎 Buy Premium (Unlimited)", callback_data="help_prem")]
    ])
    text = (
        "👋 **Welcome to UHD Tools Bot!**\n\n"
        "I am your all-in-one powerful utility bot. "
        "Free users get 5 uses/day per command.\n\n"
        "👇 **Choose a category below to explore:**"
    )
    return text, buttons

@app.on_message(filters.command("start"))
async def start(client, message):
    if not await check_fsub(client, message): return
        
    user = message.from_user
    try:
        is_new = await db.add_user(user.id, user.first_name, user.last_name, user.username)
        if is_new and Config.LOG_CHANNEL:
            await client.send_message(Config.LOG_CHANNEL, f"🚨 New User: {user.mention} (`{user.id}`)")
    except Exception as e:
        print(f"DB/Log Error: {e}")

    text, buttons = get_main_menu()
    await message.reply(text, reply_markup=buttons)

# --- CALLBACK HANDLERS (MENUS) ---

@app.on_callback_query(filters.regex("help_home"))
async def go_home(client, callback_query):
    text, buttons = get_main_menu()
    await callback_query.message.edit_text(text, reply_markup=buttons)

def back_btn():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="help_home")]])

@app.on_callback_query(filters.regex("help_pdf"))
async def help_pdf(client, callback_query):
    text = (
        "📄 **PDF PRO TOOLS**\n\n"
        "`/pdfsplit` - Extract page 1 from PDF\n"
        "`/pdf2img` - Convert PDF to Images\n"
        "`/pdftranslate hi` - Translate PDF\n"
        "`/pdftext` - Extract text from PDF\n"
        "`/pdflock pass` - Add password to PDF\n"
        "`/pdfunlock pass` - Remove PDF password"
    )
    await callback_query.message.edit_text(text, reply_markup=back_btn())

@app.on_callback_query(filters.regex("help_video"))
async def help_video(client, callback_query):
    text = (
        "🎥 **VIDEO TOOLS**\n\n"
        "`/v2a` - Extract Audio (MP3) from Video\n"
        "`/screenshot mm:ss` - Get HD frame from video"
    )
    await callback_query.message.edit_text(text, reply_markup=back_btn())

@app.on_callback_query(filters.regex("help_sec"))
async def help_sec(client, callback_query):
    text = (
        "🔐 **SECURITY & WEB**\n\n"
        "`/whois domain.com` - Get website info\n"
        "`/password 16` - Generate strong password"
    )
    await callback_query.message.edit_text(text, reply_markup=back_btn())

@app.on_callback_query(filters.regex("help_img"))
async def help_img(client, callback_query):
    text = (
        "🖼️ **IMAGE TOOLS**\n\n"
        "`/removebg` - AI Background Remover\n"
        "`/write text` - Generate handwritten note"
    )
    await callback_query.message.edit_text(text, reply_markup=back_btn())

@app.on_callback_query(filters.regex("help_file"))
async def help_file(client, callback_query):
    text = (
        "🗜️ **FILE & ZIP TOOLS**\n\n"
        "`/zip` - Compress any file to ZIP\n"
        "`/unzip` - Extract ZIP/RAR files"
    )
    await callback_query.message.edit_text(text, reply_markup=back_btn())

@app.on_callback_query(filters.regex("help_misc"))
async def help_misc(client, callback_query):
    text = (
        "🛠️ **MISC TOOLS**\n\n"
        "`/tempmail` - Get fake email\n"
        "`/inbox email` - Check temp emails\n"
        "`/quiz` - Play Math/Trivia Quiz\n"
        "`/ping` - Check Bot Ping\n"
        "`/uptime` - Check Live Uptime"
    )
    await callback_query.message.edit_text(text, reply_markup=back_btn())

@app.on_callback_query(filters.regex("help_prem"))
async def help_prem(client, callback_query):
    text = (
        "💎 **UHD PREMIUM PLAN**\n\n"
        "Free users get only 5 limits per command daily. "
        "Upgrade to Premium to get:\n\n"
        "✅ **Unlimited Command Usage**\n"
        "✅ **No Daily Restrictions**\n"
        "✅ **Priority Processing**\n\n"
        "Send `/premium` to buy the plan for just 40 Rs!"
    )
    await callback_query.message.edit_text(text, reply_markup=back_btn())

if __name__ == "__main__":
    print("Starting Keep Alive Server...")
    keep_alive()
    print("Bot is Starting...")
    app.run()
