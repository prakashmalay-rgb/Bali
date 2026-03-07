import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def search_eb116():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    dbs = await client.list_database_names()
    for db_name in dbs:
        db = client[db_name]
        colls = await db.list_collection_names()
        for coll_name in colls:
            found = await db[coll_name].find_one({'order_number': 'EB116'})
            if found:
                print(f"FOUND EB116 in DB '{db_name}', Collection '{coll_name}': {found}")

if __name__ == '__main__':
    asyncio.run(search_eb116())
