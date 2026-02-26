import uvicorn
from fastapi import FastAPI
from app.routes.main_menu_routes import router as menu_router
from app.routes.chatbot_routes import router as chat_router
from app.routes.whatsapp_routes import router as whatsapp_router
from app.routes.things_to_do_in_Bali import router as things_bali
from app.routes.event_calender import router as event_calender
from app.routes.local_cuisine import router as local_cuisine
from app.routes.what_to_do import router as what_to_do
from app.routes.plan_my_trip import router as plan_my_trip
from app.routes.language_lesson import router as language_lesson
from app.routes.websockett import router as web_order_flow
from app.routes.currency_route import router as currency_converter
from app.routes.villa_links import router as villa_links_router
from app.routes.passport_routes import router as passport_router
from app.routes.issue_routes import router as issue_router
from app.routes.onboarding import router as onboarding_router
from fastapi.middleware.cors import CORSMiddleware
from app.services.menu_services import start_cache_refresh, stop_cache_refresh
from app.services.openai_client import client
import logging


logging.basicConfig(level=logging.INFO)


app = FastAPI(
    title="Easy-Bali Chatbot",
    description="API's for easy-bali chatbot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Content-Security-Policy (CSP)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.openai.com https://*.xendit.co;"
    return response



# Include routes
app.include_router(menu_router)
app.include_router(chat_router)
app.include_router(whatsapp_router)
app.include_router(things_bali)
app.include_router(event_calender)
app.include_router(local_cuisine)
app.include_router(what_to_do)
app.include_router(plan_my_trip)
app.include_router(web_order_flow)
app.include_router(language_lesson)
app.include_router(currency_converter)
app.include_router(villa_links_router)
app.include_router(onboarding_router)
app.include_router(passport_router)
app.include_router(issue_router)

@app.on_event("startup")
def on_startup():
    start_cache_refresh()

@app.on_event("shutdown")
def on_shutdown():
    stop_cache_refresh()

@app.on_event("startup")
async def init():
    await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "System check"}]
    )

@app.get("/")
def read_root():
    return {"msg": "Welcome to EASY-BALI chatbot"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
