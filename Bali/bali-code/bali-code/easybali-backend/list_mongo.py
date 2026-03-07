import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def list_everything():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    dbs = await client.list_database_names()
    print(f"Databases: {dbs}")
    
    for db_name in dbs:
        if db_name in ['admin', 'local', 'config']:
            continue
        db = client[db_name]
        colls = await db.list_collection_names()
        print(f"DB '{db_name}' collections: {colls}")
        if 'orders-summary' in colls:
            count = await db['orders-summary'].count_documents({})
            print(f"  - orders-summary has {count} documents")
            recent = await db['orders-summary'].find().sort('_id', -1).limit(1).to_list(1)
            if recent:
                print(f"  - Most recent order in '{db_name}': {recent[0].get('order_number')}")

if __name__ == '__main__':
    asyncio.run(list_everything())
