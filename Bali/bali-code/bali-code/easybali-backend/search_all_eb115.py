import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def search_all():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    dbs = await client.list_database_names()
    for db_name in dbs:
        db = client[db_name]
        colls = await db.list_collection_names()
        for coll_name in colls:
            found = await db[coll_name].find_one({'order_number': 'EB115'})
            if found:
                print(f"FOUND EB115 in DB '{db_name}', Collection '{coll_name}': {found}")
            
            # also search by orderId or similar keys
            found2 = await db[coll_name].find_one({'orderId': 'EB115'})
            if found2:
                print(f"FOUND EB115 (orderId) in DB '{db_name}', Collection '{coll_name}': {found2}")

if __name__ == '__main__':
    asyncio.run(search_all())
