import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def list_colls():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    db = client['easybali']
    colls = await db.list_collection_names()
    print(f"COLLECTIONS: {colls}")

if __name__ == '__main__':
    asyncio.run(list_colls())
