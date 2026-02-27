from motor.motor_asyncio import AsyncIOMotorClient
from app.settings.config import settings

client = AsyncIOMotorClient(
    settings.MONGO_URII,
    serverSelectionTimeoutMS=5000,
    socketTimeoutMS=20000,
    tls=True,
    tlsAllowInvalidCertificates=True,  # Prevent SSL handshake errors on stale connections
    maxIdleTimeMS=60000  # Drop connections idle for more than a minute to avoid firewall drops
)
db = client.get_database('easybali')
order_collection = db["orders-summary"]
villa_code_collection = db['villa-codes']
passport_collection = db['passports']