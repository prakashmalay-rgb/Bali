import asyncio
from app.utils.whatsapp_func import send_whatsapp_message
from app.services.google_sheets_service import google_sheets_service
from app.services.menu_services import cache, load_data_into_cache
import pandas as pd
import re

async def check_numbers_and_notify():
    load_data_into_cache()
    df = cache.get("service_providers")
    
    clarence_info = df[df["Name"].str.contains("Clarence", case=False, na=False)]
    
    print(f"--- Raw Sheet Data ---")
    print(f"Clarence: {clarence_info['WhatsApp'].tolist() if not clarence_info.empty else 'Not Found'}")
    
    # Let's mock the number cleaning logic on Clarence's number
    cleaned_numbers = []
    if not clarence_info.empty:
        raw_num = str(clarence_info['WhatsApp'].values[0])
        clean_num = re.sub(r'[^\d]', '', raw_num)
        if clean_num.startswith('0'):
            clean_num = '62' + clean_num[1:]
        elif clean_num.startswith('8'):
            clean_num = '62' + clean_num
        cleaned_numbers.append(clean_num)
        
    print(f"\n--- Application Processed Numbers ---")
    print(f"Clarence Processed Number: {cleaned_numbers}")
    print(f"Your Processed Number: ['919840705435']")
    
if __name__ == '__main__':
    asyncio.run(check_numbers_and_notify())
