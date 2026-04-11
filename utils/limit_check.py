from database.db import db
from config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def is_limited(user_id, command_name):
    if user_id == Config.ADMIN_ID:
        return False

    is_premium, cmd_usage = await db.get_user_status(user_id, command_name)
    
    if is_premium:
        return False
        
    if cmd_usage >= 5:
        return True
    
    return False

LIMIT_TEXT = (
    "⚠️ **ᴄᴏᴍᴍᴀɴᴅ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ!**\n\n"
    "ʏᴏᴜ ʜᴀᴠᴇ ᴜsᴇᴅ **/{cmd}** 5 ᴛɪᴍᴇs ᴛᴏᴅᴀʏ.\n"
    "ғʀᴇᴇ ᴜsᴇʀs ʜᴀᴠᴇ ᴀ ʟɪᴍɪᴛ ᴏғ 5 ᴘᴇʀ ᴄᴏᴍᴍᴀɴᴅ.\n\n"
    "ᴛᴏ ɢᴇᴛ **ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss**, ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ! ✨"
)

LIMIT_BUTTON = InlineKeyboardMarkup([[InlineKeyboardButton("💎 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ", url="https://t.me/UHD_ContactBot")]])
