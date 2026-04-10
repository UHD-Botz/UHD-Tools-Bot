import os

class Config:
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    ADMIN_ID = int(os.environ.get("ADMIN_ID", ""))
    LOG_CHANNEL = os.environ.get("LOG_CHANNEL", "")
    
    FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "-1003149876834") 
    FORCE_SUB_LINK = os.environ.get("FORCE_SUB_LINK", "https://t.me/UHDBots")
    
    MONGO_URI = os.environ.get("MONGO_URI", "")
    DOWNLOAD_DIR = "./downloads"
    
    # Ensure download directory exists
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
