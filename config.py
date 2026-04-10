import os

class Config:
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
    API_ID = int(os.environ.get("API_ID", "1234567"))
    API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
    ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))
    LOG_CHANNEL = os.environ.get("LOG_CHANNEL", "-100XXXXXXXXX")
    MONGO_URI = os.environ.get("MONGO_URI", "your_mongodb_url_here")
    DOWNLOAD_DIR = "./downloads"
    
    # Ensure download directory exists
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
