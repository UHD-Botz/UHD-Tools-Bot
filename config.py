import os
import time

class Config:
    # --- BOT CORE SETTINGS ---
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    
    # 👑 ADMIN & LOGS (Integer conversion is MUST)
    # Agar env mein ID nahi milti toh default 0 set hoga
    ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
    
    # Yahan apni Log Channel ID dalo (starts with -100)
    # int() lagane se Telegram isse turant pehchan lega
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1003697134912"))
    
    # --- FORCE SUBSCRIBE SETTINGS ---
    # Isse string se number mein convert kar diya hai
    FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "@UHDBots") 
    FORCE_SUB_LINK = os.environ.get("FORCE_SUB_LINK", "https://t.me/UHDBots")
    
    # --- DATABASE & STORAGE ---
    MONGO_URI = os.environ.get("MONGO_URI", "")
    DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "./downloads")
    
    # Bot Start Time (Uptime calculate karne ke liye)
    BOT_START_TIME = time.time()

    # --- DIRECTORY SETUP ---
    # Ye check karega ki downloads folder hai ya nahi, nahi toh bana dega
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

# Tip: Agar Koyeb/Heroku use kar rahe ho toh Variables mein 
# LOG_CHANNEL aur FORCE_SUB_CHANNEL ki value bina quotes ke dalo.
