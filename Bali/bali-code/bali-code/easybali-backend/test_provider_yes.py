import asyncio
import httpx
import json

async def test_provider_yes_webhook():
    test_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "1427194068477194",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "6282247959788",
                        "phone_number_id": "681815231685748"
                    },
                    "contacts": [{
                        "profile": {"name": "Clarence"},
                        "wa_id": "923205705464"
                    }],
                    "messages": [{
                        "context": {
                            "from": "6282247959788",
                            "id": "wamid.TESTMESSAGEID126"
                        },
                        "from": "923205705464",
                        "id": "wamid.TESTMESSAGEID127",
                        "timestamp": "1772345155",
                        "type": "interactive",
                        "interactive": {
                            "type": "button_reply",
                            "button_reply": {
                                "id": "yes_order_EB71",
                                "title": "Yes"
                            }
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    async with httpx.AsyncClient() as client:
        print("🚀 Sending fake Provider Yes webhook to localhost...")
        response = await client.post("http://127.0.0.1:8000/whatsapp-webhook", json=test_payload)
        print(f"✅ Response: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    asyncio.run(test_provider_yes_webhook())
