import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import json

load_dotenv()

async def check_eb120():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    db = client['easybali']
    order = await db['orders-summary'].find_one({"order_number": "EB120"})
    if order:
        # Convert ObjectId to string for printing
        order['_id'] = str(order['_id'])
        print(json.dumps(order, indent=2, default=str))
    else:
        print("Order EB120 not found")

if __name__ == '__main__':
    asyncio.run(check_eb120())
