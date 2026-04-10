import requests
import random
import html
from pyrogram import Client, filters
from config import Config

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


# --- NEW EXTREME API QUIZ SYSTEM (100% FREE) ---
active_quizzes = {}

def fetch_extreme_quiz():
    # Sirf 2 free APIs use karenge bina kisi key ke
    apis = ['opentdb', 'trivia_api']
    choice = random.choice(apis)
    
    try:
        if choice == 'opentdb':
            # OpenTDB - Extreme Hard Multiple Choice
            res = requests.get("https://opentdb.com/api.php?amount=1&difficulty=hard&type=multiple", timeout=5).json()
            q = html.unescape(res['results'][0]['question'])
            correct = html.unescape(res['results'][0]['correct_answer'])
            options = [html.unescape(x) for x in res['results'][0]['incorrect_answers']]
            options.append(correct)
            random.shuffle(options)
            return q, options, correct
            
        elif choice == 'trivia_api':
            # The Trivia API - Hard Level
            res = requests.get("https://the-trivia-api.com/v2/questions?limit=1&difficulties=hard", timeout=5).json()
            q = res[0]['question']['text']
            correct = res[0]['correctAnswer']
            options = res[0]['incorrectAnswers'].copy()
            options.append(correct)
            random.shuffle(options)
            return q, options, correct
            
    except Exception as e:
        print(f"Quiz API Error ({choice}): {e}")
        # Agar API down ho, toh ek default extreme question
        return "What is the rarest naturally-occurring element in the Earth's crust?", ["Astatine", "Francium", "Berkelium", "Californium"], "Astatine"

@Client.on_message(filters.command("quiz"))
async def start_quiz(client, message):
    user_id = message.from_user.id
    msg = await message.reply("⏳ **Fetching an EXTREME question from Database...**")
    
    # API se naya question laao
    q, options, correct = fetch_extreme_quiz()
    
    # Options ko A, B, C, D mein format karo
    labels = ['A', 'B', 'C', 'D']
    opt_text = ""
    correct_label = ""
    
    for i, opt in enumerate(options):
        label = labels[i]
        opt_text += f"**{label})** `{opt}`\n"
        if opt == correct:
            correct_label = label
            
    # Bot memory mein sirf Sahi Letter (A/B/C/D) save karega
    active_quizzes[user_id] = correct_label 
    
    await msg.edit(
        f"😈 **EXTREME TRIVIA SURVIVAL:**\n\n"
        f"❓ `{q}`\n\n"
        f"{opt_text}\n"
        f"👉 **How to answer:** Type `/answer A`, `/answer B`, etc."
    )

@Client.on_message(filters.command("answer"))
async def check_answer(client, message):
    user_id = message.from_user.id
    
    if user_id not in active_quizzes:
        return await message.reply("⚠️ You don't have an active question! Send `/quiz` to start.")
        
    if len(message.command) < 2:
        return await message.reply("⚠️ Usage example: `/answer A`")
        
    user_ans = message.command[1].upper()
    correct_ans = active_quizzes[user_id]
    
    if user_ans == correct_ans:
        await message.reply("✅ **MIND BLOWN! Correct Answer!** 🤯 You are a true genius!")
        del active_quizzes[user_id] # Game over for this question
    else:
        await message.reply(f"❌ **WRONG!** The correct answer was **{correct_ans}**.\n\nSend `/quiz` to try another extreme question.")
        del active_quizzes[user_id] # Delete kar diya taaki cheating na kar sake 2nd try mein!
