import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.settings.config import settings
import logging

logger = logging.getLogger(__name__)

async def ensure_indexes():
    client = AsyncIOMotorClient(settings.MONGO_URII)
    db = client.get_database('easybali')
    
    # 1. Orders Summary
    logger.info("Ensuring indexes for orders-summary...")
    await db["orders-summary"].create_index("order_number", unique=True)
    await db["orders-summary"].create_index("sender_id")
    await db["orders-summary"].create_index("status")
    
    # 2. Villa Codes
    logger.info("Ensuring indexes for villa-codes...")
    await db["villa-codes"].create_index("sender_id", unique=True)
    
    # 3. Villas (Onboarding)
    logger.info("Ensuring indexes for villas...")
    await db["villas"].create_index("villa_code", unique=True)
    
    # 4. WhatsApp Queue
    logger.info("Ensuring indexes for whatsapp_message_queue...")
    await db["whatsapp_message_queue"].create_index("status")
    await db["whatsapp_message_queue"].create_index("created_at")
    
    # 5. Latency Analytics
    logger.info("Ensuring indexes for analytics_latency...")
    await db["analytics_latency"].create_index("timestamp")
    
    logger.info("✅ All indexes ensured successfully!")

if __name__ == "__main__":
    from app.settings.config import settings
    logging.basicConfig(level=logging.INFO)
    asyncio.run(ensure_indexes())
