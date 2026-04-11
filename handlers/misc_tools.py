import requests
import random
import html
import asyncio
from pyrogram import Client, filters
from config import Config
from database.db import db
from utils.limit_check import is_limited, LIMIT_TEXT, LIMIT_BUTTON, FSUB_TEXT, FSUB_BUTTON

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

@Client.on_message(filters.command("tempmail"))
async def gen_mail(client, message):
    user_id = message.from_user.id
    
    # 🚨 FSUB & LIMIT CHECK
    status = await is_limited(user_id, "tempmail", client)
    if status == "FSUB_REQUIRED":
        return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True:
        return await message.reply(LIMIT_TEXT.format(cmd="tempmail"), reply_markup=LIMIT_BUTTON)

    try:
        url = "https://api.internal.temp-mail.io/api/v3/email/new"
        res = requests.post(url, headers=HEADERS, json={"min_name_length": 10, "max_name_length": 10}, timeout=10).json()
        email = res.get('email')
        
        if not email:
            return await message.reply("❌ API returned empty response. Try again.")
            
        await message.reply(f"📧 **Your Temp Mail:** `{email}`\n\nUse `/inbox {email}` to check messages.")
        await db.increment_usage(user_id, "tempmail")
        
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
active_quizzes = {}

def fetch_extreme_quiz():
    apis = ['opentdb', 'trivia_api']
    choice = random.choice(apis)
    try:
        if choice == 'opentdb':
            res = requests.get("https://opentdb.com/api.php?amount=1&difficulty=hard&type=multiple", timeout=5).json()
            q = html.unescape(res['results'][0]['question'])
            correct = html.unescape(res['results'][0]['correct_answer'])
            options = [html.unescape(x) for x in res['results'][0]['incorrect_answers']]
            options.append(correct)
            random.shuffle(options)
            return q, options, correct
        elif choice == 'trivia_api':
            res = requests.get("https://the-trivia-api.com/v2/questions?limit=1&difficulties=hard", timeout=5).json()
            q = res[0]['question']['text']
            correct = res[0]['correctAnswer']
            options = res[0]['incorrectAnswers'].copy()
            options.append(correct)
            random.shuffle(options)
            return q, options, correct
    except Exception:
        return "What is the rarest naturally-occurring element in the Earth's crust?", ["Astatine", "Francium", "Berkelium", "Californium"], "Astatine"

@Client.on_message(filters.command("quiz"))
async def start_quiz(client, message):
    user_id = message.from_user.id
    
    status = await is_limited(user_id, "quiz", client)
    if status == "FSUB_REQUIRED":
        return await message.reply(FSUB_TEXT, reply_markup=FSUB_BUTTON)
    elif status == True:
        return await message.reply(LIMIT_TEXT.format(cmd="quiz"), reply_markup=LIMIT_BUTTON)

    msg = await message.reply("⏳ **Fetching an EXTREME question...**")
    q, options, correct = fetch_extreme_quiz()
    
    labels = ['A', 'B', 'C', 'D']
    opt_text = ""
    correct_label = ""
    for i, opt in enumerate(options):
        label = labels[i]
        opt_text += f"**{label})** `{opt}`\n"
        if opt == correct:
            correct_label = label
            
    active_quizzes[user_id] = correct_label 
    await msg.edit(f"😈 **EXTREME TRIVIA SURVIVAL:**\n\n❓ `{q}`\n\n{opt_text}\n👉 **How to answer:** Type `/answer A`")
    await db.increment_usage(user_id, "quiz")

@Client.on_message(filters.command("answer"))
async def check_answer(client, message):
    user_id = message.from_user.id
    if user_id not in active_quizzes:
        return await message.reply("⚠️ No active quiz! Send `/quiz` to start.")
    if len(message.command) < 2:
        return await message.reply("⚠️ Usage: `/answer A`")
        
    user_ans = message.command[1].upper()
    correct_ans = active_quizzes[user_id]
    
    if user_ans == correct_ans:
        await message.reply("✅ **MIND BLOWN! Correct Answer!** 🤯")
        await db.update_score(user_id, 10)
    else:
        await message.reply(f"❌ **WRONG!** The correct answer was **{correct_ans}**.")
    del active_quizzes[user_id]
