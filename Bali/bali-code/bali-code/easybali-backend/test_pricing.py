import asyncio
import httpx

async def test_locations():
    base_url = "http://localhost:8000/menu/price_distribution"
    service = "Deep Tissue Massage 90 mins"
    
    zones = ["Zone 1", "Zone 2", "Ubud", "Canggu", "Seminyak"]
    
    async with httpx.AsyncClient() as client:
        for zone in zones:
            print(f"\n--- Testing Zone: {zone} ---")
            try:
                # Add location_zone to params
                params = {"service_item": service, "location_zone": zone}
                response = await client.get(base_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    print(f"Service: {data.get('service_item')}")
                    print(f"Vendor Price: {data.get('service_provider_price')}")
                    print(f"Villa Comm (Applied Rate): {data.get('villa_price')}")
                    print(f"Applied Zone Strategy: {data.get('applied_zone')}")
                else:
                    print(f"Failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_locations())
