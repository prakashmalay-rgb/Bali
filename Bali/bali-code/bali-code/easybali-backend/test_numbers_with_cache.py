import asyncio
import os
from app.utils.whatsapp_func import fetch_whatsapp_numbers
from app.services.menu_services import load_data_into_cache
from dotenv import load_dotenv

load_dotenv()

async def test_numbers():
    load_data_into_cache()
    service = "Balinese Massage - 60min"
    numbers = await fetch_whatsapp_numbers(service)
    print(f"NUMBERS FOR '{service}': {numbers}")

if __name__ == '__main__':
    asyncio.run(test_numbers())
