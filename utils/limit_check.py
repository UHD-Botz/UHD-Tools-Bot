from database.db import db
from config import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, PeerIdInvalid

async def is_limited(user_id, command_name, client=None):
    if user_id == Config.ADMIN_ID:
        return False

    # 📡 FSUB CHECK
    if client and Config.FORCE_SUB_CHANNEL:
        try:
            await client.get_chat_member(Config.FORCE_SUB_CHANNEL, user_id)
        except UserNotParticipant:
            return "FSUB_REQUIRED"
        except PeerIdInvalid:
            # Agar Peer ID invalid aaye toh error ignore karo taaki bot ruke nahi
            pass
        except Exception as e:
            print(f"FSub Logic Error: {e}")

    # 📊 LIMIT & DB CHECK (Safe Mode)
    try:
        is_premium, cmd_usage = await db.get_user_status(user_id, command_name)
        if is_premium:
            return False
        if cmd_usage >= 5:
            return True
        return False
    except Exception as e:
        print(f"Database Connection Error: {e}")
        # Agar socket error/DB error aaye toh bot command process na kare aur user ko bata de
        return "DB_ERROR"

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
