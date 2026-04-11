from database.db import db
from config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, PeerIdInvalid

async def is_limited(user_id, command_name, client=None):
    # 👑 Admin is always free
    if user_id == Config.ADMIN_ID:
        return False

    # 📡 FORCE SUBSCRIBE CHECK & PEER RECOGNITION
    if client:
        try:
            # Ye line Peer ID ko bot ki memory mein refresh karegi
            chat = await client.get_chat(Config.FORCE_SUB_CHANNEL)
            
            # Check if user joined
            try:
                await client.get_chat_member(chat.id, user_id)
            except UserNotParticipant:
                return "FSUB_REQUIRED" # Signal for FSub
        except PeerIdInvalid:
            print(f"⚠️ Peer ID still invalid for {Config.FORCE_SUB_CHANNEL}. Forward a message from channel to bot!")
        except Exception as e:
            print(f"FSub Logic Error: {e}")

    # 📊 LIMIT CHECK LOGIC
    is_premium, cmd_usage = await db.get_user_status(user_id, command_name)
    
    if is_premium:
        return False
        
    if cmd_usage >= 5:
        return True
    
    return False

# --- UI ELEMENTS ---
LIMIT_TEXT = (
    "⚠️ **ᴄᴏᴍᴍᴀɴᴅ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ!**\n\n"
    "ʏᴏᴜ ʜᴀᴠᴇ ᴜsᴇᴅ **/{cmd}** 5 ᴛɪᴍᴇs ᴛᴏᴅᴀʏ.\n"
    "ғʀᴇᴇ ᴜsᴇʀs ʜᴀᴠᴇ ᴀ ʟɪᴍɪᴛ ᴏғ 5 ᴘᴇʀ ᴄᴏᴍᴍᴀɴᴅ.\n\n"
    "ᴛᴏ ɢᴇᴛ **ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss**, ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ! ✨"
)

LIMIT_BUTTON = InlineKeyboardMarkup([[
    InlineKeyboardButton("💎 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ", url="https://t.me/UHD_ContactBot")
]])

FSUB_TEXT = (
    "❌ **ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ!**\n\n"
    "ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ.\n"
    "ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ!"
)

FSUB_BUTTON = InlineKeyboardMarkup([[
    InlineKeyboardButton("📢 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=Config.FORCE_SUB_LINK)
]])
