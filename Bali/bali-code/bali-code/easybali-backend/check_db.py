import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    db = client['easybali']
    order = await db['orders-summary'].find_one({'order_number': 'EB115'})
    print(f"ORDER_DEETS: {order}")

if __name__ == '__main__':
    asyncio.run(check())
