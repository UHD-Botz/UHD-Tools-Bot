import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from config import Config
from database.db import db

# --- PREMIUM UI ---
PREMIUM_TEXT = """🚀 **UHD Search Bot Premium**

➠ **Mode** : Purchase
➠ **Price** : 40 Rs. / Month
➠ **Benefits** : Unlimited Access + Channel/Group Support

➠ **How To Buy** ❓ : 
1. Scan the QR Code and Pay 40 Rs.
2. Wait 30 Seconds.
3. Click On The 'Verify Payment' Button.
4. Send Your Payment UTR / Transaction ID For Activation.

For Any Queries Contact: @UHD_ContactBot"""

PREMIUM_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("✅ Verify Payment", callback_data="verify_pay")],
    [InlineKeyboardButton("📖 Get UTR Guide", callback_data="utr_guide"),
     InlineKeyboardButton("📞 Contact Us", url="https://t.me/UHD_ContactBot")]
])

@Client.on_message(filters.command("premium"))
async def premium_cmd(client, message):
    # QR Code image path (Apne bot folder mein qr.jpg naam ki image rakhna)
    qr_path = "qr.jpg" 
    if os.path.exists(qr_path):
        await message.reply_photo(photo=qr_path, caption=PREMIUM_TEXT, reply_markup=PREMIUM_BUTTONS)
    else:
        await message.reply_text(PREMIUM_TEXT, reply_markup=PREMIUM_BUTTONS)

@Client.on_callback_query(filters.regex("verify_pay"))
async def verify_cb(client, callback_query):
    await callback_query.message.reply_text(
        "📝 **sᴇɴᴅ ʏᴏᴜʀ ᴜᴛʀ / ᴛʀᴀɴsᴀᴄᴛɪᴏɴ ɪᴅ ʙᴇʟᴏᴡ ᴛᴏ ᴠᴇʀɪғʏ.**\n\n"
        "⚠️ **ɴᴏᴛᴇ:** ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴇxᴀᴄᴛʟʏ 40 ʀs., ᴏᴛʜᴇʀᴡɪsᴇ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ᴡɪʟʟ ғᴀɪʟ!\n\n"
        "❌ ᴛʏᴘᴇ `/cancel` ᴛᴏ sᴛᴏᴘ ᴛʜᴇ ᴘʀᴏᴄᴇss.",
        reply_markup=ForceReply(True) # Isse user seedha reply karega
    )

# --- UTR COLLECTION ---
@Client.on_message(filters.reply & filters.text)
async def utr_receiver(client, message):
    if "sᴇɴᴅ ʏᴏᴜʀ ᴜᴛʀ" in message.reply_to_message.text:
        utr_id = message.text
        user = message.from_user
        
        await message.reply_text("⏳ **Your UTR has been sent to Admin for verification. Please wait!**")
        
        # Log Channel Alert with Approve/Reject Buttons
        log_btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")]
        ])
        
        await client.send_message(
            Config.LOG_CHANNEL,
            f"💰 **NEW PAYMENT ALERT**\n\n"
            f"👤 **User:** {user.mention} (`{user.id}`)\n"
            f"🆔 **UTR:** `{utr_id}`\n"
            f"💵 **Amount:** 40 Rs.\n\n"
            f"Verify the UTR in your bank/app and take action below:",
            reply_markup=log_btns
        )
