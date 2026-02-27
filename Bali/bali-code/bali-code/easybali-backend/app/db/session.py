from motor.motor_asyncio import AsyncIOMotorClient
from app.settings.config import settings

import certifi

# Use certifi to explicitly provide trusted root certificates.
# This fixes the MongoDB Atlas [SSL: TLSV1_ALERT_INTERNAL_ERROR] timeout issues on Render.
client = AsyncIOMotorClient(
    settings.MONGO_URII,
    serverSelectionTimeoutMS=5000,
    socketTimeoutMS=20000,
    tls=True,
    tlsCAFile=certifi.where(),  # Provides Mozilla's root CA bundle for trusted SSL handshake
    maxIdleTimeMS=60000  # Drop connections idle for more than a minute
)
db = client.get_database('easybali')
order_collection = db["orders-summary"]
villa_code_collection = db['villa-codes']
passport_collection = db['passports']