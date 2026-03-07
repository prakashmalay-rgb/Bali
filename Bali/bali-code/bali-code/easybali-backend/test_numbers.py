import asyncio
import os
from app.utils.whatsapp_func import fetch_whatsapp_numbers
from dotenv import load_dotenv

load_dotenv()

async def test_numbers():
    service = "Balinese Massage - 60min"
    numbers = await fetch_whatsapp_numbers(service)
    print(f"NUMBERS FOR '{service}': {numbers}")

if __name__ == '__main__':
    asyncio.run(test_numbers())
