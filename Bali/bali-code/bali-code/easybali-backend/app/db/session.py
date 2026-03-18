from motor.motor_asyncio import AsyncIOMotorClient
from app.settings.config import settings

import certifi
import urllib.parse

# Atlas URL construction
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
checkin_collection = db['checkins']
issue_collection = db['issues']
inquiry_collection = db['inquiries']
feedback_collection = db['feedback']
content_collection = db['content_library']
customer_collection = db['customers']