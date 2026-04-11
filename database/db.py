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

# Ise apni Database class ke andar add karna hai
    async def set_premium(self, user_id: int, status: bool):
        await self.users.update_one(
            {"_id": user_id},
            {"$set": {"is_premium": status}},
            upsert=True
        )
    
    # --- 💎 PREMIUM & LIMIT METHODS ---

    async def get_user_status(self, user_id, command_name):
        user = await self.users.find_one({"_id": user_id})
        if user:
            is_premium = user.get("is_premium", False)
            # Har command ka alag count nikalega
            usage_dict = user.get("usage_dict", {})
            cmd_usage = usage_dict.get(command_name, 0)
            return is_premium, cmd_usage
        return False, 0

    async def increment_usage(self, user_id, command_name):
        # Specific command ka count +1 karega
        await self.users.update_one(
            {"_id": user_id}, 
            {"$inc": {f"usage_dict.{command_name}": 1}}
        )

    async def reset_daily_usage(self):
        # Poori dictionary khali kar dega
        await self.users.update_many({}, {"$set": {"usage_dict": {}}})
        

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
