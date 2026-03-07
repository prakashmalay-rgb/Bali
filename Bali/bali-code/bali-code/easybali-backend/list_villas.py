import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def list_villas():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    db = client['easybali']
    villas = await db['villa-codes'].find().limit(5).to_list(5)
    for v in villas:
        print(f"VILLA: {v}")

if __name__ == '__main__':
    asyncio.run(list_villas())
