import asyncio
from app.services.menu_services import load_data_into_cache, get_service_providers, get_service_overview

async def check():
    load_data_into_cache()
    sp = await get_service_providers()
    overview = await get_service_overview()
    print("--- Services Providers ---")
    print(sp[['Number', 'Name', 'WhatsApp']].head(10))
    print("\n--- Services Overview (Partial) ---")
    print(overview[overview["Service Item"].str.contains("Balinese Massage", na=False)][['Service Item', 'Service Providers']])

if __name__ == "__main__":
    asyncio.run(check())
