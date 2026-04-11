from database.db import db
from config import Config

async def is_limited(user_id):
    # 👑 OWNER BYPASS: Admin ke liye koi limit nahi
    if user_id == Config.ADMIN_ID:
        return False

    is_premium, usage = await db.get_user_status(user_id)
    
    if is_premium:
        return False
        
    if usage >= 5:
        return True
    
    return False
