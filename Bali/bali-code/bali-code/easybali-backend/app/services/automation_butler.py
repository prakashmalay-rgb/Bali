from app.db.session import db
from app.services.whatsapp_queue import enqueue_whatsapp_message
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

order_collection = db["orders-summary"]
template_collection = db["message_templates"]

async def process_automations():
    """
    Background worker that runs hourly to scan for guests needing messages.
    """
    while True:
        try:
            now = datetime.utcnow()
            logger.info("🤖 Butler: Scanning for guest automations...")
            
            # 1. Welcome Message (Sent within 1 hour of booking or scheduled check-in)
            # 2. Mid-Stay Check-in (Stay duration / 2)
            # 3. Pre-Checkout (18 hours before)
            # 4. Post-Checkout (6 hours after)
            
            # Query for active guests
            async for order in order_collection.find({"status": "paid"}):
                await check_order_triggers(order, now)
                
        except Exception as e:
            logger.error(f"Butler Error: {e}")
            
        await asyncio.sleep(3600) # Run every hour

async def check_order_triggers(order, now):
    villa_code = order.get("villa_code")
    phone = order.get("phone")
    guest_name = order.get("guest_name", "Guest")
    
    # We use a set of sent_triggers to avoid duplicates
    sent = order.get("sent_automations", [])
    
    # Example: Pre-Checkout Trigger (18 hours before check_out)
    if "pre_checkout" not in sent:
        check_out = order.get("check_out_date") # Assuming stored as datetime
        if check_out and (check_out - now) < timedelta(hours=18):
            template_content = await get_template(villa_code, "pre_checkout")
            if template_content:
                message = template_content.format(name=guest_name)
                await enqueue_whatsapp_message(phone, message)
                await mark_sent(order["_id"], "pre_checkout")

    # Example: Welcome Message
    if "welcome" not in sent:
        created_at = order.get("created_at")
        if created_at and (now - created_at) < timedelta(hours=1):
            template_content = await get_template(villa_code, "welcome")
            if template_content:
                message = template_content.format(name=guest_name)
                await enqueue_whatsapp_message(phone, message)
                await mark_sent(order["_id"], "welcome")

async def get_template(villa_code, trigger_type):
    # Fetch customized template or fallback to default
    tpl = await template_collection.find_one({"villa_code": villa_code, "type": trigger_type})
    if tpl:
        if not tpl.get("is_active", True):
            return None
        return tpl["content"]
        
    # If no db record exists, assume disabled by default to prevent unwanted spam
    return None

async def mark_sent(order_id, trigger_name):
    await order_collection.update_one(
        {"_id": order_id},
        {"$addToSet": {"sent_automations": trigger_name}}
    )
