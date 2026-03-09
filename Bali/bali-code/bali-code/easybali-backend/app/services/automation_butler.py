from app.db.session import db
from app.services.whatsapp_queue import enqueue_whatsapp_message
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

order_collection = db["orders-summary"]
checkin_collection = db["checkins"]
passport_collection = db["passports"]
template_collection = db["message_templates"]

async def process_automations():
    """
    Background worker that runs hourly to scan for guests needing messages.
    """
    while True:
        try:
            now = datetime.now()
            logger.info("🤖 Butler: Scanning for guest automations...")
            
            # 1. Process Orders
            async for order in order_collection.find({"status": "PAID"}):
                await check_order_triggers(order, now)
                
            # 2. Process Check-ins (Task 18: Passport reminders etc)
            async for checkin in checkin_collection.find({"status": "active"}):
                await check_checkin_triggers(checkin, now)
                
        except Exception as e:
            logger.error(f"Butler Error: {e}")
            
        await asyncio.sleep(3600) # Run every hour

async def check_checkin_triggers(checkin, now):
    sender_id = checkin.get("sender_id")
    villa_code = checkin.get("villa_code")
    checkin_time = checkin.get("checkin_time")
    sent = checkin.get("sent_automations", [])

    # Passport Reminder (1 hour after checkin if no passport found)
    if "passport_reminder" not in sent:
        if checkin_time and (now - checkin_time) > timedelta(hours=1):
            # Check if passport exists
            existing = await passport_collection.find_one({"user_id": sender_id})
            if not existing:
                reminder_msg = (
                    "👋 *A Friendly Reminder*\n\n"
                    "We noticed you haven't submitted your passport yet. It's required for local registration.\n\n"
                    "Please upload a clear photo of your passport here on WhatsApp. 📄"
                )
                await enqueue_whatsapp_message(sender_id, reminder_msg)
                await mark_checkin_sent(checkin["_id"], "passport_reminder")

async def mark_checkin_sent(checkin_id, trigger_name):
    await checkin_collection.update_one(
        {"_id": checkin_id},
        {"$addToSet": {"sent_automations": trigger_name}}
    )

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

    # Mid-Stay Suggestion (3 days after creation if not checked out)
    if "mid_stay" not in sent:
        created_at = order.get("created_at")
        if created_at and (now - created_at) > timedelta(days=3):
            message = f"🌴 Hi {guest_name}, we hope you're having a wonderful stay! Need a relaxing massage or a private driver for tomorrow? Just type *Order Services* to explore."
            await enqueue_whatsapp_message(phone, message)
            await mark_sent(order["_id"], "mid_stay")

    # Feedback Request (6 hours after check_out)
    if "feedback_request" not in sent:
        check_out = order.get("check_out_date")
        if check_out and (now - check_out) > timedelta(hours=6):
            message = f"👋 Hi {guest_name}, thank you for staying with us! We'd love to hear about your experience. How was your stay and our concierge service? (Reply directly here)"
            await enqueue_whatsapp_message(phone, message)
            await mark_sent(order["_id"], "feedback_request")

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
