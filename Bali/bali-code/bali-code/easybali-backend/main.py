from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Core services ──────────────────────────────────────────────────────────────
from app.services.menu_services import start_cache_refresh, stop_cache_refresh
from app.services.openai_client import client
from app.settings.config import settings

# ── Core Chatbot Routers (MUST succeed — no silent fallback here) ──────────────
from app.routes.chatbot_routes import router as chatbot_router
from app.routes.whatsapp_routes import router as whatsapp_router
from app.routes.currency_route import router as currency_router
from app.routes.event_calender import router as event_calender_router
from app.routes.language_lesson import router as language_lesson_router
from app.routes.local_cuisine import router as local_cuisine_router
from app.routes.main_menu_routes import router as main_menu_router
from app.routes.plan_my_trip import router as plan_my_trip_router
from app.routes.things_to_do_in_Bali import router as things_bali_router
from app.routes.villa_links import router as villa_links_router
from app.routes.websockett import router as websocket_router
from app.routes.what_to_do import router as what_to_do_router
from app.routes.onboarding import router as onboarding_router
from app.routes.passport_routes import router as passport_router
from app.routes.issue_routes import router as issue_router

# ── App Initialization ─────────────────────────────────────────────────────────
app = FastAPI(
    title="EASY Bali Backend",
    description="API for EASY Bali Chatbot, Host Dashboard, WhatsApp AI, and Xendit Integration",
    version="2.0.0"
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security Headers ──────────────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# ── Register Core Routers ─────────────────────────────────────────────────────
app.include_router(chatbot_router)
app.include_router(whatsapp_router)
app.include_router(currency_router)
app.include_router(event_calender_router)
app.include_router(language_lesson_router)
app.include_router(local_cuisine_router)
app.include_router(main_menu_router)
app.include_router(plan_my_trip_router)
app.include_router(things_bali_router)
app.include_router(villa_links_router)
app.include_router(websocket_router)
app.include_router(what_to_do_router)
app.include_router(onboarding_router)
app.include_router(passport_router)
app.include_router(issue_router)

# ── Register Optional Routers (safe imports) ──────────────────────────────────
try:
    from app.routes.admin_routes import router as admin_router
    app.include_router(admin_router)
    logger.info("✅ admin_routes loaded")
except Exception as e:
    logger.error(f"❌ admin_routes failed: {e}")

try:
    from app.routes.dashboard_routes import router as dashboard_router
    app.include_router(dashboard_router)
    logger.info("✅ dashboard_routes loaded")
except Exception as e:
    logger.error(f"❌ dashboard_routes failed: {e}")

try:
    from app.routes.admin_users import router as admin_users_router
    app.include_router(admin_users_router)
    logger.info("✅ admin_users loaded")
except Exception as e:
    logger.error(f"❌ admin_users failed: {e}")

try:
    from app.routes.xendit_webhook import router as xendit_router
    app.include_router(xendit_router)
    logger.info("✅ xendit_webhook loaded")
except Exception as e:
    logger.error(f"❌ xendit_webhook failed: {e}")

try:
    from app.routes.promo_admin import router as promo_admin_router
    app.include_router(promo_admin_router)
    logger.info("✅ promo_admin_router loaded")
except Exception as e:
    logger.error(f"❌ promo_admin_router failed: {e}")

try:
    from app.routes.faq_admin import router as faq_admin_router
    app.include_router(faq_admin_router)
    logger.info("✅ faq_admin_router loaded")
except Exception as e:
    logger.error(f"❌ faq_admin_router failed: {e}")

try:
    from app.routes.automation_admin import router as automation_admin_router
    app.include_router(automation_admin_router)
    logger.info("✅ automation_admin_router loaded")
except Exception as e:
    logger.error(f"❌ automation_admin_router failed: {e}")

# ── Startup / Shutdown ────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("Starting cache refresh service...")
    start_cache_refresh()

    import asyncio

    try:
        from app.services.whatsapp_queue import whatsapp_queue
        asyncio.create_task(whatsapp_queue.process_queue())
        logger.info("🚀 WhatsApp message queue processor started!")
    except Exception as e:
        logger.warning(f"WhatsApp queue not started: {e}")

    try:
        from app.services.automation_butler import process_automations
        asyncio.create_task(process_automations())
        logger.info("🤖 Automation Butler started!")
    except Exception as e:
        logger.warning(f"Automation butler not started: {e}")

    try:
        await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[{"role": "system", "content": "System check"}]
        )
        logger.info("✅ OpenAI check successful!")
    except Exception as e:
        logger.error(f"❌ OpenAI check failed: {e}")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Stopping cache refresh service...")
    stop_cache_refresh()

# ── Root / Healthcheck ─────────────────────────────────────────────────────────
@app.api_route("/", methods=["GET", "HEAD"], tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": "EASY Bali API v2",
        "message": "All systems operational."
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)