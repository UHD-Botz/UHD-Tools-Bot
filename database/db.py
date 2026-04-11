import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

class Database:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users = self.db.users # MongoDB Collection for users

    async def add_user(self, user_id, first_name, last_name=None, username=None):
        user = await self.users.find_one({"_id": user_id})
        
        if not user:
            # Naya user: Premium False aur Usage 0 se start hoga
            user_data = {
                "_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "join_date": datetime.datetime.now(),
                "score": 0,
                "is_premium": False, # Default Free
                "usage_count": 0,    # Default 0 tasks
                "is_banned": False 
            }
            await self.users.insert_one(user_data)
            return True 
        else:
            # Purana user: Update info without resetting premium/usage
            await self.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "first_name": first_name, 
                    "last_name": last_name, 
                    "username": username
                }}
            )
            return False

    # --- 💎 PREMIUM & LIMIT METHODS ---

    async def get_user_status(self, user_id):
        """User ka premium status aur usage count nikalne ke liye"""
        user = await self.users.find_one({"_id": user_id})
        if user:
            # Agar purane user ke DB mein ye fields nahi hain, toh default return karo
            is_premium = user.get("is_premium", False)
            usage = user.get("usage_count", 0)
            return is_premium, usage
        return False, 0

    async def increment_usage(self, user_id):
        """Har task ke baad usage count badhane ke liye"""
        await self.users.update_one({"_id": user_id}, {"$inc": {"usage_count": 1}})

    async def set_premium(self, user_id, status=True):
        """User ko premium dene ya hatane ke liye"""
        await self.users.update_one(
            {"_id": user_id}, 
            {"$set": {"is_premium": status, "usage_count": 0}}
        )

    async def reset_daily_usage(self):
        """Saare free users ka limit reset karne ke liye"""
        await self.users.update_many({}, {"$set": {"usage_count": 0}})

    # --- 🧠 QUIZ SCORE METHODS ---
    async def update_score(self, user_id, points):
        await self.users.update_one({"_id": user_id}, {"$inc": {"score": points}})

    async def get_score(self, user_id):
        user = await self.users.find_one({"_id": user_id})
        return user.get("score", 0) if user else 0

    # --- 📊 ADMIN / STATS METHODS ---
    async def get_all_users(self):
        return await self.users.find().to_list(length=None)
        
    async def total_users_count(self):
        return await self.users.count_documents({})

db = Database(Config.MONGO_URI, "UHDToolsBot")
