from fastapi import APIRouter, HTTPException
from app.schemas.ai_response import ChatbotQuery
from app.services.ai_prompt import generate_response
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/currency-converter", tags=["Chatbot"])

_TRACKED_CURRENCIES = ["IDR", "EUR", "GBP", "SGD", "AUD", "JPY", "CNY", "MYR", "THB", "CHF"]

async def _fetch_live_rates() -> str:
    """
    Fetch current exchange rates from open.er-api.com (free, no key required).
    Returns a compact rate string to inject into the AI prompt.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://open.er-api.com/v6/latest/USD")
            if resp.status_code == 200:
                rates = resp.json().get("rates", {})
                parts = []
                for cur in _TRACKED_CURRENCIES:
                    if cur in rates:
                        parts.append(f"1 USD = {rates[cur]:,.2f} {cur}")
                if parts:
                    return "Live rates: " + " | ".join(parts)
    except Exception as e:
        logger.warning(f"Live rate fetch failed: {e}")
    return ""


@router.post("/chat")
async def chat_endpoint(request: ChatbotQuery, user_id: str):
    """
    Currency Converter Chat — injects live exchange rates so the AI
    converts amounts accurately rather than using training-data estimates.
    """
    user_query = request.query
    if not user_query:
        raise HTTPException(status_code=400, detail="No query provided.")

    live_rates = await _fetch_live_rates()

    # Prepend live rates as context so the AI does exact math
    enriched_query = f"[{live_rates}]\n{user_query}" if live_rates else user_query

    try:
        return await generate_response(
            query=enriched_query,
            user_id=user_id,
            chat_type="currency-converter",
            language=request.language
        )
    except Exception as e:
        logger.error(f"Currency converter error: {e}")
        return {"response": "Sorry, I couldn't process your conversion request. Please try again."}
