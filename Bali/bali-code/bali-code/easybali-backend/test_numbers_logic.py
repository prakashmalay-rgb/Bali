import asyncio
from app.utils.whatsapp_func import fetch_whatsapp_numbers
from app.services.menu_services import load_data_into_cache

async def test():
    load_data_into_cache()
    service_name = "Balinese Massage - 60min"
    numbers = await fetch_whatsapp_numbers(service_name)
    print(f"Numbers for '{service_name}': {numbers}")
    
    service_name_alt = "Balinese Massage   60min" # test robustness
    numbers_alt = await fetch_whatsapp_numbers(service_name_alt)
    print(f"Numbers for '{service_name_alt}': {numbers_alt}")

if __name__ == "__main__":
    asyncio.run(test())
