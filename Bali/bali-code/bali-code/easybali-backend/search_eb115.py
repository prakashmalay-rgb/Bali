import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    db = client['easybali']
    colls = await db.list_collection_names()
    for coll_name in colls:
        found = await db[coll_name].find_one({'order_number': 'EB115'})
        if found:
            print(f"FOUND EB115 in {coll_name}: {found}")

if __name__ == '__main__':
    asyncio.run(check())
