from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

try:
    from app.routes import (
        whatsapp_routes, xendit_webhook, chatbot_routes, currency_route, event_calender, 
        language_lesson, local_cuisine, main_menu_routes, plan_my_trip, things_to_do_in_Bali, 
        villa_links, websockett, what_to_do
    )
except ImportError as e:
    logging.warning(f"Could not import some routes: {e}")

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EASY Bali Backend",
    description="API for EASY Bali Whatsapp Bot, Host Dashboard, and Xendit Integration",
    version="1.0.0"
)

# Set up CORS for the frontend dashboard
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # Vite dev server
    "https://www.easy-bali.com",
    "https://easy-bali.onrender.com",
    "https://bali-v92r.onrender.com",
    "https://bali-3o33wubjp-prakashmalay-4140s-projects.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root/Healthcheck
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": "EASY Bali API",
        "message": "Production-grade backend initialized successfully.",
    }

# Register Routers safely
try:
    app.include_router(whatsapp_routes.router)
    app.include_router(chatbot_routes.router)
    app.include_router(currency_route.router)
    app.include_router(event_calender.router)
    app.include_router(language_lesson.router)
    app.include_router(local_cuisine.router)
    app.include_router(main_menu_routes.router)
    app.include_router(plan_my_trip.router)
    app.include_router(things_to_do_in_Bali.router)
    app.include_router(villa_links.router)
    app.include_router(websockett.router)
    app.include_router(what_to_do.router)
    
    from app.routes import dashboard_routes
    app.include_router(dashboard_routes.router)
except NameError as e:
    logger.error(f"Skipping some router registrations due to import errors: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)