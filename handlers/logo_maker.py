import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- 3D LOGO MAKER PLUGIN ---

@Client.on_message(filters.command("3dlogo"))
async def make_logo_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply("⚠️ **Text toh daal mere bhai!**\nExample: `/3dlogo Fjtdtdjsgjyd`")
        
    logo_text = message.text.split(None, 1)[1]
    
    if len(logo_text) > 15:
        return await message.reply("⚠️ Text thoda chota rakh bhai (Max 15 chars), varna logo ganda dikhega.")

    # 1. First Confirmation (Jaisa tune screenshot mein dikhaya)
    await message.reply(f"✅ **What to do? :** {logo_text}")

    # 2. Style Selection Menu
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💧 Text on wet glass", callback_data=f"logo|wetglass|{logo_text}"),
         InlineKeyboardButton("🌈 Colorful neon text", callback_data=f"logo|neon|{logo_text}")],
        [InlineKeyboardButton("⚙️ Digital glitch text", callback_data=f"logo|glitch|{logo_text}"),
         InlineKeyboardButton("🔥 Naruto Text", callback_data=f"logo|naruto|{logo_text}")],
        [InlineKeyboardButton("👑 Luxury gold text", callback_data=f"logo|gold|{logo_text}"),
         InlineKeyboardButton("🏖️ Text on sand", callback_data=f"logo|sand|{logo_text}")],
        [InlineKeyboardButton("🌊 3D Text underwater", callback_data=f"logo|water|{logo_text}"),
         InlineKeyboardButton("🎆 Text fireWork", callback_data=f"logo|firework|{logo_text}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="close_logo_menu")]
    ])
    
    await message.reply(
        f"**Choose Logos :** {logo_text}",
        reply_markup=buttons
    )

# --- API INTEGRATION & IMAGE GENERATION ---

@Client.on_callback_query(filters.regex(r"^logo\|"))
async def process_logo_style(client, callback_query):
    # Button se data nikalna
    data = callback_query.data.split("|")
    style = data[1]
    logo_text = data[2]
    
    processing_msg = await callback_query.message.edit_text(
        f"⏳ **Generating your 3D Logo...**\n🎨 Style: `{style}`\n📝 Text: `{logo_text}`\n\n*Server se connect ho raha hu, thoda wait kar...*"
    )

    # 🌐 Yahan Hum API Call Karenge (Example using a free API structure)
    # Note: Free APIs ke endpoints change hote rehte hain. 
    # Agar ye API band ho jaye, toh tu Siputzx ya Botcahx ka link yahan daal sakta hai.
    
    api_url = f"https://api.siputzx.my.id/api/textpro/{style}?text={logo_text}"
    
    try:
        # aiohttp se async request (Bot hang nahi hoga)
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                
                if response.status == 200:
                    # Agar API direct image bhejti hai:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'image' in content_type:
                        image_data = await response.read() # Image download kar li
                        
                        await processing_msg.delete()
                        await client.send_photo(
                            chat_id=callback_query.message.chat.id,
                            photo=image_data,
                            caption=f"✅ **Logo Generated!**\n✨ **Style:** {style.title()}\n📝 **Text:** {logo_text}\n\n🤖 @{client.me.username}"
                        )
                    else:
                        # Agar API JSON response bhejti hai (jinme image ka link hota hai)
                        res_json = await response.json()
                        image_link = res_json.get("result") or res_json.get("url")
                        
                        if image_link:
                            await processing_msg.delete()
                            await client.send_photo(
                                chat_id=callback_query.message.chat.id,
                                photo=image_link,
                                caption=f"✅ **Logo Generated!**\n✨ **Style:** {style.title()}\n📝 **Text:** {logo_text}\n\n🤖 @{client.me.username}"
                            )
                        else:
                            await processing_msg.edit_text("❌ API ne image nahi di. Shayad ye style is API par available nahi hai.")
                else:
                    await processing_msg.edit_text(f"❌ Server Down Hai! Status Code: {response.status}\nBaad mein try kar.")
                    
    except Exception as e:
        await processing_msg.edit_text(f"❌ Connection Error: `{e}`\nLagta hai free API band ho gayi hai.")

# --- CANCEL BUTTON HANDLER ---
@Client.on_callback_query(filters.regex("close_logo_menu"))
async def close_logo_menu(client, callback_query):
    await callback_query.message.delete()
