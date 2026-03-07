import asyncio
import httpx
from app.settings.config import settings

async def send_direct_test():
    numbers = ["919840705435", "923205705464"]
    
    headers = {
        "Authorization": f"Bearer {settings.access_token}",
        "Content-Type": "application/json"
    }
    
    for number in numbers:
        payload = {
            "messaging_product": "whatsapp",
            "to": number,
            "type": "text",
            "text": {
                "body": "👋 Hello! This is a test message from EASYBali verifying your number is correctly registered in the system."
            }
        }
        
        async with httpx.AsyncClient() as client:
            print(f"🚀 Sending direct test message to {number}...")
            response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(send_direct_test())
