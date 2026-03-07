import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def list_recent_orders():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    db = client['easybali']
    orders = await db['orders-summary'].find().sort('created_at', -1).limit(5).to_list(5)
    for o in orders:
        print(f"ORDER: {o.get('order_number')} | {o.get('service_name')} | Status: {o.get('status')} | Confirmed: {o.get('confirmation')}")

if __name__ == '__main__':
    asyncio.run(list_recent_orders())
