from app.db.session import db
from app.services.whatsapp_queue import enqueue_whatsapp_message
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

order_collection      = db["orders-summary"]
checkin_collection    = db["checkins"]
passport_collection   = db["passports"]
template_collection   = db["message_templates"]
guest_reg_collection  = db["guest_registrations"]

# ── Hardcoded fallback defaults (used when DB template is inactive/missing) ───

_DEFAULTS = {
    "passport_reminder": (
        "👋 *A Friendly Reminder*\n\n"
        "We noticed you haven't submitted your passport yet. It's required for local registration.\n\n"
        "Please upload a clear photo of your passport here on WhatsApp. 📄"
    ),
    "day_1_welcome": (
        "🌴 *Welcome to your first full day!*\n\n"
        "We hope you're settling in perfectly. If you need fresh towels, pool cleaning, or local tips, just let me know!\n\n"
        "Have a wonderful day in Bali. ✨"
    ),
    "mid_stay_concierge": (
        "☀️ *Time for an adventure?*\n\n"
        "You've been with us for a few days now! If you'd like to book a private tour, a spa treatment, or a driver for dinner, I'm here to help.\n\n"
        "Just type *Order Services* to explore our curated Bali experiences. 🥥"
    ),
    "pre_checkout_remind": (
        "👋 *Planning your departure?*\n\n"
        "We hope you've enjoyed your stay! Your checkout is coming up soon. 🕑\n\n"
        "Would you like us to arrange an *Airport Transfer* or a driver for your next stop?\n"
        "Type *Order Services* to book your ride now."
    ),
    "feedback_request": (
        "⭐ *We'd love your feedback!*\n\n"
        "Thank you for choosing Easy-Bali. On a scale of *1–5*, how was your experience at the villa and with our concierge service?\n\n"
        "Your feedback helps us provide a better experience for future guests! 🙏"
    ),
    "pre_arrival": (
        "🌺 *Your Bali stay begins soon!*\n\n"
        "Hi {name}, we are getting your villa ready for your arrival!\n\n"
        "Here's what to expect:\n"
        "• Scan the QR code at the villa entrance to check in\n"
        "• WiFi details and orientation guide will be shared on arrival\n"
        "• Your AI concierge activates the moment you check in\n"
        "• Directions: {maps_link}\n\n"
        "What time do you expect to arrive? Reply with your ETA (e.g., *3 PM*). See you soon! 🥥"
    ),
}


# ── Template fetcher ──────────────────────────────────────────────────────────

async def get_template(villa_code: str, trigger_type: str) -> str:
    """
    Return active template content for (villa_code, trigger_type).
    Falls back to hardcoded default if not found or marked inactive.
    """
    tpl = await template_collection.find_one({"villa_code": villa_code, "type": trigger_type})
    if tpl and tpl.get("is_active", False):
        return tpl["content"]
    return _DEFAULTS.get(trigger_type, "")


def _apply_vars(msg: str, sender_id: str = "", guest_name: str = "", maps_link: str = "") -> str:
    name = guest_name or f"Guest ...{sender_id[-4:]}" if sender_id else "Guest"
    msg = msg.replace("{name}", name)
    if maps_link:
        msg = msg.replace("{maps_link}", maps_link)
    else:
        msg = msg.replace("\n• Directions: {maps_link}", "")
    return msg


# ── Main background loop ──────────────────────────────────────────────────────

async def process_automations():
    """Background worker — runs every hour."""
    while True:
        try:
            now = datetime.now()
            logger.info("🤖 Butler: Scanning for guest automations...")

            # 1. Pre-arrival (before guests arrive)
            await check_pre_arrival_triggers(now)

            # 2. Active check-ins
            async for checkin in checkin_collection.find({"status": "active"}):
                await check_checkin_triggers(checkin, now)

        except Exception as e:
            logger.error(f"Butler Error: {e}")

        await asyncio.sleep(3600)


# ── Pre-arrival: scan guest_registrations ────────────────────────────────────

async def check_pre_arrival_triggers(now: datetime):
    """Send pre-arrival WhatsApp 24–48 hours before registered check-in date."""
    async for reg in guest_reg_collection.find({"status": "expected", "pre_arrival_sent": {"$ne": True}}):
        sender_id  = reg.get("sender_id")
        villa_code = reg.get("villa_code")
        checkin_dt = reg.get("checkin_date")
        guest_name = reg.get("guest_name", "")

        if not sender_id or not checkin_dt:
            continue

        hours_until = (checkin_dt - now).total_seconds() / 3600
        if 0 < hours_until <= 48:
            msg = await get_template(villa_code, "pre_arrival")
            villa_profile = await db["villa_profiles"].find_one({"villa_code": villa_code}) or {}
            maps_link = villa_profile.get("maps_link", "")
            msg = _apply_vars(msg, sender_id, guest_name, maps_link)
            await enqueue_whatsapp_message(sender_id, msg)
            await guest_reg_collection.update_one(
                {"_id": reg["_id"]},
                {"$set": {
                    "pre_arrival_sent": True,
                    "pre_arrival_sent_at": now,
                    "awaiting_eta": True,
                }}
            )
            logger.info(f"Butler: pre_arrival sent to {sender_id} ({villa_code})")


# ── Check-in lifecycle triggers ───────────────────────────────────────────────

async def check_checkin_triggers(checkin: dict, now: datetime):
    sender_id  = checkin.get("sender_id")
    villa_code = checkin.get("villa_code")
    checkin_time = checkin.get("checkin_time")
    sent = checkin.get("sent_automations", [])

    if not checkin_time or not sender_id:
        return

    # 1. Passport reminder — 1 hour after check-in, only if no passport submitted
    if "passport_reminder" not in sent:
        if (now - checkin_time) > timedelta(hours=1):
            existing = await passport_collection.find_one({"user_id": sender_id})
            if not existing:
                msg = await get_template(villa_code, "passport_reminder")
                await enqueue_whatsapp_message(sender_id, _apply_vars(msg, sender_id))
                await mark_checkin_sent(checkin["_id"], "passport_reminder")

    # 2. Day-1 welcome — 24 hours after check-in
    if "day_1_welcome" not in sent:
        if (now - checkin_time) > timedelta(hours=24):
            msg = await get_template(villa_code, "day_1_welcome")
            await enqueue_whatsapp_message(sender_id, _apply_vars(msg, sender_id))
            await mark_checkin_sent(checkin["_id"], "day_1_welcome")

    # 3. Mid-stay concierge — 72 hours after check-in
    if "mid_stay_concierge" not in sent:
        if (now - checkin_time) > timedelta(hours=72):
            msg = await get_template(villa_code, "mid_stay_concierge")
            await enqueue_whatsapp_message(sender_id, _apply_vars(msg, sender_id))
            await mark_checkin_sent(checkin["_id"], "mid_stay_concierge")

    # ── Resolve checkout date ─────────────────────────────────────────────────
    latest_order = await order_collection.find_one(
        {"sender_id": sender_id, "status": "PAID"},
        sort=[("created_at", -1)]
    )
    checkout_date = latest_order.get("check_out_date") if latest_order else None
    estimated_checkout = checkout_date or (checkin_time + timedelta(days=5))

    if not checkin.get("estimated_checkout"):
        await checkin_collection.update_one(
            {"_id": checkin["_id"]},
            {"$set": {"estimated_checkout": estimated_checkout}}
        )

    # 4. Pre-checkout reminder — 20 hours before estimated checkout
    if "pre_checkout_remind" not in sent:
        time_left = estimated_checkout - now
        if timedelta(hours=0) < time_left < timedelta(hours=20):
            msg = await get_template(villa_code, "pre_checkout_remind")
            await enqueue_whatsapp_message(sender_id, _apply_vars(msg, sender_id))
            await mark_checkin_sent(checkin["_id"], "pre_checkout_remind")

    # 4b. Key return reminder — sent 2 hours before checkout
    if "key_return_remind" not in sent:
        time_left = estimated_checkout - now
        if timedelta(hours=0) < time_left < timedelta(hours=2):
            key_msg = (
                "🔑 *Checkout Reminder*\n\n"
                "Just a quick note — please remember to leave all villa keys at the front entrance "
                "or in the key box before you depart.\n\n"
                "Safe travels and we hope to see you again in Bali! 🌴"
            )
            await enqueue_whatsapp_message(sender_id, key_msg)
            await mark_checkin_sent(checkin["_id"], "key_return_remind")

    # 5. Checkout summary — 1–4 hours after estimated checkout
    if "checkout_summary" not in sent:
        hours_since = (now - estimated_checkout).total_seconds() / 3600
        if 1 <= hours_since < 4:
            paid_orders = await order_collection.find(
                {"sender_id": sender_id, "villa_code": villa_code, "status": "PAID"}
            ).to_list(20)

            if paid_orders:
                lines = "\n".join(
                    f"• {o.get('service_name', 'Service')} — IDR {o.get('payment', {}).get('paid_amount', 0):,.0f}"
                    for o in paid_orders
                )
                total = sum(o.get("payment", {}).get("paid_amount", 0) for o in paid_orders)
                summary_msg = (
                    f"🧾 *Your Stay Summary*\n\n"
                    f"Thank you for staying with us at *{villa_code}*!\n\n"
                    f"*Services Used:*\n{lines}\n\n"
                    f"*Total Spent:* IDR {total:,.0f}\n\n"
                    f"We hope you had a wonderful time in Bali! 🌴"
                )
                await enqueue_whatsapp_message(sender_id, summary_msg)
            await mark_checkin_sent(checkin["_id"], "checkout_summary")

    # 6. Feedback request — 4–24 hours after estimated checkout
    if "feedback_request" not in sent:
        hours_since = (now - estimated_checkout).total_seconds() / 3600
        if 4 <= hours_since < 24:
            msg = await get_template(villa_code, "feedback_request")
            await enqueue_whatsapp_message(sender_id, _apply_vars(msg, sender_id))
            await mark_checkin_sent(checkin["_id"], "feedback_request")
            await checkin_collection.update_one(
                {"_id": checkin["_id"]},
                {"$set": {"status": "completed"}}
            )


# ── Helpers ───────────────────────────────────────────────────────────────────

async def mark_checkin_sent(checkin_id, trigger_name: str):
    await checkin_collection.update_one(
        {"_id": checkin_id},
        {"$addToSet": {"sent_automations": trigger_name}}
    )


async def check_order_triggers(order: dict, now: datetime):
    # Kept for future non-QR service-specific flows.
    pass
