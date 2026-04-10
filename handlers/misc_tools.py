import requests
import random
from pyrogram import Client, filters

# --- TEMP MAIL (NEW API) ---
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

@Client.on_message(filters.command("tempmail"))
async def gen_mail(client, message):
    try:
        # Naya API jo Koyeb par block nahi hoga
        url = "https://api.internal.temp-mail.io/api/v3/email/new"
        res = requests.post(url, headers=HEADERS, json={"min_name_length": 10, "max_name_length": 10}, timeout=10).json()
        email = res.get('email')
        
        if not email:
            return await message.reply("❌ API returned empty response. Try again.")
            
        await message.reply(f"📧 **Your Temp Mail:** `{email}`\n\nUse `/inbox {email}` to check messages.")
    except Exception as e:
        await message.reply(f"❌ **TempMail API Error:** `{e}`")

@Client.on_message(filters.command("inbox"))
async def check_inbox(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/inbox youremail@domain.com`")
    
    email = message.command[1]
    
    try:
        url = f"https://api.internal.temp-mail.io/api/v3/email/{email}/messages"
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        
        if not res:
            return await message.reply("📭 Inbox is empty. (Wait a few seconds and try again)")
        
        text = "📥 **Inbox Messages:**\n\n"
        for msg in res[:5]:
            text += f"**From:** {msg.get('from', 'Unknown')}\n**Subject:** {msg.get('subject', 'No Subject')}\n\n"
        await message.reply(text)
    except Exception as e:
        await message.reply(f"❌ **Could not fetch inbox:** `{e}`")


# --- QUIZ SYSTEM ---
questions = {"What is 15 * 4?": "60", "Solve: 100 / 4 + 5": "30", "Square root of 144?": "12"}

@Client.on_message(filters.command("quiz"))
async def start_quiz(client, message):
    q = random.choice(list(questions.keys()))
    await message.reply(f"🧠 **Math Quiz:**\n`{q}`\n\nReply with: `/answer <your_answer>`")

@Client.on_message(filters.command("answer"))
async def check_answer(client, message):
    if not message.reply_to_message or "Math Quiz:" not in message.reply_to_message.text:
        return await message.reply("⚠️ Reply to a quiz question with `/answer <your_answer>`")
    
    try:
        user_ans = message.command[1]
        question_text = message.reply_to_message.text.split("\n")[1].strip("`")
        
        correct_ans = questions.get(question_text)
        if user_ans == correct_ans:
            await message.reply("✅ **Correct Answer!** Brilliant!")
        else:
            await message.reply(f"❌ **Wrong!** The correct answer was: `{correct_ans}`")
    except IndexError:
        await message.reply("Usage: `/answer <your_answer>`")
