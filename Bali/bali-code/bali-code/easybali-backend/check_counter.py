import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check_counter():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    db = client['easybali']
    counter = await db.counters.find_one({'_id': 'order_number'})
    print(f"COUNTER: {counter}")

if __name__ == '__main__':
    asyncio.run(check_counter())
