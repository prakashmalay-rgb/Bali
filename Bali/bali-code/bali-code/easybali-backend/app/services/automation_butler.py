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

    if not checkin_time or not sender_id:
        return

    # 1. Passport Reminder (1 hour after check-in if no passport found)
    if "passport_reminder" not in sent:
        if (now - checkin_time) > timedelta(hours=1):
            existing = await passport_collection.find_one({"user_id": sender_id})
            if not existing:
                reminder_msg = (
                    "👋 *A Friendly Reminder*\n\n"
                    "We noticed you haven't submitted your passport yet. It's required for local registration.\n\n"
                    "Please upload a clear photo of your passport here on WhatsApp. 📄"
                )
                await enqueue_whatsapp_message(sender_id, reminder_msg)
                await mark_checkin_sent(checkin["_id"], "passport_reminder")

    # 2. Day 1 Welcome (24 hours after check-in) - Task 20
    if "day_1_welcome" not in sent:
        if (now - checkin_time) > timedelta(hours=24):
            welcome_msg = (
                "🌴 *Welcome to your first full day!*\n\n"
                "We hope you're settling in perfectly. If you need any fresh towels, pool cleaning, or local tips, just let me know! Have a wonderful day in Bali. ✨"
            )
            await enqueue_whatsapp_message(sender_id, welcome_msg)
            await mark_checkin_sent(checkin["_id"], "day_1_welcome")

    # 3. Mid-stay Activation (72 hours/3 days after check-in) - Task 20
    if "mid_stay_concierge" not in sent:
        if (now - checkin_time) > timedelta(hours=72):
            mid_msg = (
                "☀️ *Time for an adventure?*\n\n"
                "You've been with us for a few days now! If you'd like to book a private tour, a spa treatment, or a driver for dinner, I'm here to help.\n\n"
                "Just type *Order Services* to explore our curated Bali experiences. 🥥"
            )
            await enqueue_whatsapp_message(sender_id, mid_msg)
            await mark_checkin_sent(checkin["_id"], "mid_stay_concierge")

    # 4. Pre-checkout & Logistics (Try to detect checkout from orders) - Task 21
    # Check if guest has a PAID booking with a checkout date
    latest_order = await order_collection.find_one(
        {"sender_id": sender_id, "status": "PAID"},
        sort=[("created_at", -1)]
    )
    
    checkout_date = latest_order.get("check_out_date") if latest_order else None
    
    # If no explicit checkout date, assume typical 5-day stay for fallback logic
    estimated_checkout = checkout_date or (checkin_time + timedelta(days=5))

    # Update checkin doc with estimated checkout for dashboard visibility
    if not checkin.get("estimated_checkout"):
        await checkin_collection.update_one(
            {"_id": checkin["_id"]},
            {"$set": {"estimated_checkout": estimated_checkout}}
        )

    if "pre_checkout_remind" not in sent:
        # Send 20 hours before checkout
        if (estimated_checkout - now) < timedelta(hours=20) and (estimated_checkout - now) > timedelta(hours=0):
            checkout_msg = (
                "👋 *Planning your departure?*\n\n"
                "We hope you've enjoyed your stay! Your checkout is scheduled soon. 🕑\n\n"
                "Would you like us to arrange an *Airport Transfer* or a driver for your next stop? "
                "Type *Order Services* to book your ride now."
            )
            await enqueue_whatsapp_message(sender_id, checkout_msg)
            await mark_checkin_sent(checkin["_id"], "pre_checkout_remind")

    # 5. Feedback Request (Post-checkout) - Task 22
    if "feedback_request" not in sent:
        # Send 4 hours after estimated checkout
        if (now - estimated_checkout) > timedelta(hours=4) and (now - estimated_checkout) < timedelta(hours=24):
            feedback_msg = (
                "⭐ *We'd love your feedback!*\n\n"
                "Thank you for choosing Easy-Bali. On a scale of 1-5, how was your experience at the villa and with our concierge service?\n\n"
                "Your feedback helps us provide a better experience for future guests! 🙏"
            )
            await enqueue_whatsapp_message(sender_id, feedback_msg)
            await mark_checkin_sent(checkin["_id"], "feedback_request")
            
            # Deactivate checkin once all automations are done
            await checkin_collection.update_one({"_id": checkin["_id"]}, {"$set": {"status": "completed"}})

async def mark_checkin_sent(checkin_id, trigger_name):
    await checkin_collection.update_one(
        {"_id": checkin_id},
        {"$addToSet": {"sent_automations": trigger_name}}
    )

async def check_order_triggers(order, now):
    # Already handled by checkin_triggers for arrivals, 
    # but kept for non-QR arrivals or service-specific flows.
    pass

async def get_template(villa_code, trigger_type):
    # Fetch customized template or fallback to default
    tpl = await template_collection.find_one({"villa_code": villa_code, "type": trigger_type})
    if tpl:
        if not tpl.get("is_active", True):
            return None
        return tpl["content"]
        
    return None

async def mark_sent(order_id, trigger_name):
    await order_collection.update_one(
        {"_id": order_id},
        {"$addToSet": {"sent_automations": trigger_name}}
    )
