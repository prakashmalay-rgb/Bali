from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
import httpx
from app.db.session import db
from app.settings.config import settings

class WhatsAppQueue:
    def __init__(self):
        self.collection = db["whatsapp_message_queue"]
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    async def enqueue(self, recipient_id: str, payload: Dict[str, Any], message_type: str = "text"):
        """Add a message to the queue"""
        message_data = {
            "recipient_id": recipient_id,
            "payload": payload,
            "message_type": message_type,
            "status": "pending",
            "retry_count": 0,
            "errors": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await self.collection.insert_one(message_data)
        return str(result.inserted_id)

    async def process_queue(self):
        """Background worker to process pending messages"""
        while True:
            try:
                # Find pending or failed messages that still have retries
                messages = self.collection.find({
                    "status": {"$in": ["pending", "failed"]},
                    "retry_count": {"$lt": self.max_retries}
                }).sort("created_at", 1).limit(10)

                async for msg in messages:
                    await self.send_message_with_retry(msg)
                
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                print(f"Error in WhatsApp queue processor: {e}")
                await asyncio.sleep(30)

    async def send_message_with_retry(self, msg_record: Dict[str, Any]):
        msg_id = msg_record["_id"]
        recipient_id = msg_record["recipient_id"]
        payload = msg_record["payload"]
        
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
                response.raise_for_status()
                
                # Success
                await self.collection.update_one(
                    {"_id": msg_id},
                    {
                        "$set": {
                            "status": "sent",
                            "sent_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                print(f"✅ Message sent from queue to {recipient_id}")
                
        except Exception as e:
            error_msg = str(e)
            retry_count = msg_record["retry_count"] + 1
            status = "failed" if retry_count >= self.max_retries else "retry_pending"
            
            await self.collection.update_one(
                {"_id": msg_id},
                {
                    "$set": {
                        "status": status,
                        "retry_count": retry_count,
                        "updated_at": datetime.utcnow()
                    },
                    "$push": {
                        "errors": {
                            "attempt": retry_count,
                            "error": error_msg,
                            "timestamp": datetime.utcnow()
                        }
                    }
                }
            )
            print(f"❌ Failed to send message to {recipient_id} (Attempt {retry_count}): {error_msg}")

# Global instance
whatsapp_queue = WhatsAppQueue()
