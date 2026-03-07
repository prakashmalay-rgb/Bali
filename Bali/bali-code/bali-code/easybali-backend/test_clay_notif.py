import asyncio
import httpx
from app.settings.config import settings

async def test_user_notification():
    # User's test number
    phone_number = "919840705435"
    order_id = "EB-TEST-999"
    
    headers = {
        "Authorization": f"Bearer {settings.access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": "🛎️ New Booking Request (Real Test)"
            },
            "body": {
                "text": f"Service: Balinese Massage\nDate: 2026-03-07\nTime: 14:00\nPrice: IDR 20,000\n\nOrder ID: {order_id}"
            },
            "footer": {
                "text": "Confirm to receive payment link"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": order_id, # MUST match order_number exactly
                            "title": "✅ Accept"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"decline_{order_id}",
                            "title": "❌ Decline"
                        }
                    }
                ]
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        print(f"🚀 Sending test notification for {order_id} to {phone_number}...")
        response = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("✅ SUCCESS: Test message sent! Please click 'Accept' then 'Yes'.")
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_user_notification())
