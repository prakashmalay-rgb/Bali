import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def check():
    uri = os.getenv("MONGO_URII")
    client = AsyncIOMotorClient(uri)
    dbs = await client.list_database_names()
    print(f"DATABASES: {dbs}")
    
    for db_name in dbs:
        db = client[db_name]
        colls = await db.list_collection_names()
        print(f"DATABASE {db_name} COLLECTIONS: {colls}")
        
if __name__ == '__main__':
    asyncio.run(check())
