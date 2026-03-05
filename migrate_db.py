import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def migrate():
    source_uri = "mongodb+srv://4772hassan:txI6i6DkVVHA3GGl@easybalicluster.qcpk7.mongodb.net/"
    dest_uri = "mongodb+srv://prakashmalay_db_user:QbBqlWv1K676Y9V4@easybali.xvindoa.mongodb.net/"
    
    print("Connecting to databases...")
    source_client = AsyncIOMotorClient(source_uri)
    dest_client = AsyncIOMotorClient(dest_uri)
    
    source_db = source_client.get_database('easybali')
    dest_db = dest_client.get_database('easybali')
    
    collections = await source_db.list_collection_names()
    print(f"Collections to migrate: {collections}")
    
    for coll_name in collections:
        print(f"Migrating collection: {coll_name}...")
        source_collection = source_db[coll_name]
        dest_collection = dest_db[coll_name]
        
        # clear destination collection to avoid duplicates if run multiple times
        await dest_collection.delete_many({})
        
        cursor = source_collection.find({})
        # fetch all documents
        docs = await cursor.to_list(length=None)
        
        if docs:
            await dest_collection.insert_many(docs)
            print(f"  ✓ Successfully migrated {len(docs)} documents to {coll_name}")
        else:
            print(f"  - No documents found in {coll_name}")

if __name__ == "__main__":
    asyncio.run(migrate())
