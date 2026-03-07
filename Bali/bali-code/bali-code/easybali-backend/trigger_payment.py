import asyncio
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from app.utils.whatsapp_func import create_xendit_payment_with_distribution, send_interactive_message
from app.models.order_summary import Order
from app.db.session import order_collection

load_dotenv()

async def trigger_acceptance():
    from app.services.menu_services import load_data_into_cache
    print("📥 Loading sheets data into cache...")
    load_data_into_cache()
    
    order_num = "EB-TEST-999"
    sender_id = "919840705435"
    
    print(f"🔄 Manually triggering acceptance for {order_num}...")
    
    # 1. Fetch order from DB
    order_data = await order_collection.find_one({"order_number": order_num})
    if not order_data:
        print(f"❌ Order {order_num} not found in DB.")
        return

    # 2. Update order as confirmed (Simulating Service Provider Acceptance)
    await order_collection.update_one(
        {"order_number": order_num},
        {"$set": {"confirmation": True, "status": "confirmed"}}
    )
    
    # 3. Generate Xendit Payment Link
    try:
        order = Order(**order_data)
        print(f"🔗 Generating Xendit Payment Link...")
        payment_result = await create_xendit_payment_with_distribution(order)
        
        if payment_result.get('success'):
            print(f"✅ SUCCESS! Payment URL: {payment_result['payment_url']}")
            
            # 4. Send the link to the user's WhatsApp
            print(f"📱 Sending link to WhatsApp {sender_id}...")
            await send_interactive_message(sender_id, payment_result)
            print("✨ DONE! Check your WhatsApp.")
        else:
            print(f"❌ Xendit Error: {payment_result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error during payment generation: {e}")

if __name__ == "__main__":
    asyncio.run(trigger_acceptance())
