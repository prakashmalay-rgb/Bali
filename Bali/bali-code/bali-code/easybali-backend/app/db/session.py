from motor.motor_asyncio import AsyncIOMotorClient
from app.settings.config import settings

import certifi
import urllib.parse

# Safely inject connection resilience parameters directly into the Atlas connection string.
# Motor/PyMongo often ignore **kwargs when connecting to mongodb+srv:// endpoints.
uri = settings.MONGO_URII
if "?" in uri:
    uri += "&tls=true&tlsAllowInvalidCertificates=true&serverSelectionTimeoutMS=5000&connectTimeoutMS=10000"
else:
    uri += "?tls=true&tlsAllowInvalidCertificates=true&serverSelectionTimeoutMS=5000&connectTimeoutMS=10000"

client = AsyncIOMotorClient(uri, tlsCAFile=certifi.where())
db = client.get_database('easybali')
order_collection = db["orders-summary"]
villa_code_collection = db['villa-codes']
passport_collection = db['passports']