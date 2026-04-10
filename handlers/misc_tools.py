import requests
import random
from pyrogram import Client, filters

# --- TEMP MAIL ---
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

@Client.on_message(filters.command("tempmail"))
async def gen_mail(client, message):
    try:
        res = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1", headers=headers, timeout=10).json()
        email = res[0]
        await message.reply(f"📧 **Your Temp Mail:** `{email}`\n\nUse `/inbox {email}` to check messages.")
    except Exception as e:
        await message.reply("❌ **TempMail API is currently down. Please try again later.**")

@Client.on_message(filters.command("inbox"))
async def check_inbox(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/inbox youremail@domain.com`")
    
    email = message.command[1]
    if "@" not in email: return await message.reply("Invalid Email format.")
    
    login, domain = email.split('@')
    try:
        res = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}", headers=headers, timeout=10).json()
        
        if not res:
            return await message.reply("📭 Inbox is empty.")
        
        text = "📥 **Inbox Messages:**\n\n"
        for msg in res[:5]:
            text += f"**From:** {msg['from']}\n**Subject:** {msg['subject']}\n**ID:** `{msg['id']}`\n\n"
        await message.reply(text)
    except Exception as e:
        await message.reply("❌ **Could not connect to inbox. Try again later.**")

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
