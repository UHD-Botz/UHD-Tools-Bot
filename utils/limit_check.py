from database.db import db
from config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def is_limited(user_id):
    # 👑 OWNER BYPASS: Admin ke liye koi limit nahi
    if user_id == Config.ADMIN_ID:
        return False

    is_premium, usage = await db.get_user_status(user_id)
    
    # Premium users ke liye koi limit nahi
    if is_premium:
        return False
        
    # Free users: 5 task ki limit
    if usage >= 5:
        return True
    
    return False

# ⚠️ YE WOH VARIABLES HAIN JO MISSING DIKHA RAHA HAI
LIMIT_TEXT = (
    "⚠️ **ᴅᴀɪʟʏ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ!**\n\n"
    "ғʀᴇᴇ ᴜsᴇʀs ᴄᴀɴ ᴏɴʟʏ ᴜsᴇ 5 ᴛᴀsᴋs ᴘᴇʀ ᴅᴀʏ.\n"
    "ᴛᴏ ɢᴇᴛ **ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss**, ʙᴜʏ ᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ! ✨"
)

LIMIT_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("💎 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ", url="https://t.me/UHD_ContactBot")]
])
