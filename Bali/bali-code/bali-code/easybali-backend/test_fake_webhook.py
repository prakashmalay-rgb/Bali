import asyncio
import httpx
import json

async def test_flow_webhook():
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
                        "profile": {"name": "Test User"},
                        "wa_id": "919840705435"
                    }],
                    "messages": [{
                        "from": "919840705435",
                        "id": "wamid.TESTMESSAGEID123",
                        "type": "interactive",
                        "interactive": {
                            "type": "nfm_reply",
                            "nfm_reply": {
                                "response_json": json.dumps({
                                    "flow_token": "hkjhkhkjhkhkjhkjhkjk",
                                    "selected_service": "Balinese Massage - 60min",
                                    "selected_date": "15-03-2026",
                                    "person_selection": "2",
                                    "time_selection": "10:00 AM to 12:00 PM",
                                    "status": "booking_completed"
                                }),
                                "body": "Sent",
                                "name": "flow"
                            }
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    async with httpx.AsyncClient() as client:
        print("🚀 Sending fake Flow webhook to localhost...")
        response = await client.post("http://127.0.0.1:8000/whatsapp-webhook", json=test_payload)
        print(f"✅ Response: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    asyncio.run(test_flow_webhook())
