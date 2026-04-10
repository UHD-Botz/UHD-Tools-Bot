from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

class Database:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users = self.db.users

    async def add_user(self, user_id, name):
        user = await self.users.find_one({"_id": user_id})
        if not user:
            await self.users.insert_one({"_id": user_id, "name": name, "score": 0})
            return True
        return False

    async def update_score(self, user_id, points):
        await self.users.update_one({"_id": user_id}, {"$inc": {"score": points}})

    async def get_score(self, user_id):
        user = await self.users.find_one({"_id": user_id})
        return user["score"] if user else 0

db = Database(Config.MONGO_URI, "UHDToolsBot")
