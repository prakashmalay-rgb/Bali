import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

async def create_test_order():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    db = client['easybali']
    col = db['orders-summary']
    
    order_number = "EB-TEST-999"
    sender_id = "919840705435"
    
    await col.delete_many({"order_number": order_number})
    
    test_order = {
        "order_number": order_number,
        "service_name": "Balinese Massage - 60min",
        "sender_id": sender_id,
        "date": datetime(2026, 3, 7),
        "time": "14:00",
        "price": "20,000",
        "confirmation": False,
        "status": "pending",
        "villa_code": "V1", # Valid code
        "created_at": datetime.now()
    }
    
    await col.insert_one(test_order)
    print(f"✅ Created real-test order {order_number} for sender {sender_id} with Villa V1")

if __name__ == '__main__':
    asyncio.run(create_test_order())
