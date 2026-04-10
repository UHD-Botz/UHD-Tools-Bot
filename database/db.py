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
            # Agar naya user hai toh saari details insert karenge
            user_data = {
                "_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "join_date": datetime.datetime.now(),
                "score": 0,
                "is_banned": False # Future me kisi ko block karne ke kaam aayega
            }
            await self.users.insert_one(user_data)
            return True # Returns True for new user
        else:
            # Agar purana user hai, toh bas uska naam/username update kar denge (incase usne change kiya ho)
            await self.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "first_name": first_name, 
                    "last_name": last_name, 
                    "username": username
                }}
            )
            return False

    # --- QUIZ SCORE METHODS ---
    async def update_score(self, user_id, points):
        await self.users.update_one({"_id": user_id}, {"$inc": {"score": points}})

    async def get_score(self, user_id):
        user = await self.users.find_one({"_id": user_id})
        return user.get("score", 0) if user else 0

    # --- ADMIN / BROADCAST METHODS ---
    async def get_all_users(self):
        # Broadcast ke liye saare users ki list
        return await self.users.find().to_list(length=None)
        
    async def total_users_count(self):
        # /stats command ke liye total user count
        return await self.users.count_documents({})

db = Database(Config.MONGO_URI, "UHDToolsBot")
