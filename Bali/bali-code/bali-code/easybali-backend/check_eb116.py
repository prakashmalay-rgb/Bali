import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check_eb116():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    db = client['easybali']
    order = await db['orders-summary'].find_one({'order_number': 'EB116'})
    print(f"ORDER EB116: {order}")

if __name__ == '__main__':
    asyncio.run(check_eb116())
