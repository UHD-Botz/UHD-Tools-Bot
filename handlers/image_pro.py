import os
from pyrogram import Client, filters
from rembg import remove
from config import Config
from database.db import db
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON, FSUB_TEXT, FSUB_BUTTON

@Client.on_message(filters.command(["removebg", "rmbg"]))
async def bg_remove(client, message):
    user_id = message.from_user.id
    status = await is_limited(user_id, "removebg", client)
    if status == "FSUB_REQUIRED": return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True: return await message.reply(LIMIT_TEXT.format(cmd="removebg"), reply_markup=LIMIT_BUTTON)

    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply("⚠️ **Reply to an Image with `/removebg`**")

    msg = await message.reply("⏳ **AI Processing... Removing Background...**")
    file_path = await message.reply_to_message.download()
    out_path = f"{Config.DOWNLOAD_DIR}/nobg_{user_id}.png"
    
    try:
        with open(file_path, 'rb') as i:
            input_img = i.read()
        output_img = remove(input_img)
        
        with open(out_path, 'wb') as o:
            o.write(output_img)
            
        await client.send_document(message.chat.id, out_path, caption="🪄 **Background Removed!**\n\n🛡️ @UHDBots")
        await msg.delete()
        await db.increment_usage(user_id, "removebg")
    except Exception as e: await msg.edit(f"❌ **Error:** `{e}`")
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(out_path): os.remove(out_path)
