import os
import requests
from pyrogram import Client, filters
from config import Config
from database.db import db
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON, FSUB_TEXT, FSUB_BUTTON

@Client.on_message(filters.command(["removebg", "rmbg"]))
async def bg_remove(client, message):
    user_id = message.from_user.id
    
    # Check limit safely
    status = await is_limited(user_id, "removebg", client)
    if status == "FSUB_REQUIRED": return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True: return await message.reply(LIMIT_TEXT.format(cmd="removebg"), reply_markup=LIMIT_BUTTON)
    elif status == "DB_ERROR": return await message.reply("❌ **Database Disconnected!** Please try again later.")

    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply("⚠️ **Usage:** Reply to an Image with `/removebg`")

    # 🔥 KOYEB SE API KEY UTHANE KA LOGIC
    API_KEY = os.environ.get("REMOVE_BG_API_KEY", "")
    if not API_KEY:
        return await message.reply("❌ **Admin Error:** Koyeb mein `REMOVE_BG_API_KEY` set nahi hai!")

    msg = await message.reply("⏳ **Sending to Cloud for Processing...**")
    file_path = await message.reply_to_message.download()
    out_path = f"{Config.DOWNLOAD_DIR}/nobg_{user_id}.png"
    
    try:
        with open(file_path, 'rb') as img_file:
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': img_file},
                data={'size': 'auto'},
                headers={'X-Api-Key': API_KEY},
            )
        
        if response.status_code == requests.codes.ok:
            with open(out_path, 'wb') as out_file:
                out_file.write(response.content)
            await client.send_document(message.chat.id, out_path, caption="🪄 **Background Removed!**\n\n🛡️ @UHDBots")
            await msg.delete()
            await db.increment_usage(user_id, "removebg")
        else:
            await msg.edit(f"❌ **API Error:** `{response.text}`")
            
    except Exception as e: await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)
