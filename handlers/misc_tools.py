import requests
import random
from pyrogram import Client, filters
from database.db import db

# --- TEMP MAIL ---
@Client.on_message(filters.command("tempmail"))
async def gen_mail(client, message):
    res = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1").json()
    email = res[0]
    await message.reply(f"📧 **Your Temp Mail:** `{email}`\n\nUse `/inbox {email}` to check messages.")

@Client.on_message(filters.command("inbox"))
async def check_inbox(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/inbox youremail@domain.com`")
    
    email = message.command[1]
    login, domain = email.split('@')
    res = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}").json()
    
    if not res:
        return await message.reply("📭 Inbox is empty.")
    
    text = "📥 **Inbox Messages:**\n\n"
    for msg in res[:5]: # Show top 5
        text += f"**From:** {msg['from']}\n**Subject:** {msg['subject']}\n**ID:** `{msg['id']}`\n\n"
    await message.reply(text)

# --- QUIZ SYSTEM ---
questions = [
    {"q": "What is 15 * 4?", "a": "60"},
    {"q": "Solve: 100 / 4 + 5", "a": "30"},
    {"q": "Square root of 144?", "a": "12"}
]

@Client.on_message(filters.command("quiz"))
async def start_quiz(client, message):
    q = random.choice(questions)
    await message.reply(f"🧠 **Math Quiz:**\n{q['q']}\n\nReply with `/answer <your_answer> <question_text>` to check!")

@Client.on_message(filters.command("write"))
async def writer(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/write <topic>`")
    topic = " ".join(message.command[1:])
    template = f"📚 **Assignment on {topic.title()}**\n\n{topic.title()} is a fascinating subject that encompasses various elements of our modern world. Understanding {topic} is crucial for grasping broader concepts in its field. This brief overview serves as an introduction to the vast depths of {topic}."
    await message.reply(template)
