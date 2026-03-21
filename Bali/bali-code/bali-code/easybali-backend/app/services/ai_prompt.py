import json
import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from app.settings.config import settings
from app.services.menu_services import cache
from app.services.openai_client import client
from app.utils.chat_memory import get_conversation_history, trim_history, save_message
from app.services.pinconeservice import get_index
from app.utils.navigation_rules import rules
from app.services.ai_menu_generator import ai_menu_generator
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

# Specialized System Personas for different Chat Types
PERSONAS = {
    "what-to-do": """
        You’re EasyBali, Bali’s most enthusiastic travel pal!
        Vibe: Friendly, witty, local.
        Mission: Suggest specific activities for the guest based on their mood, time of day, and location.
        Check the INTERNAL DB (Services sheet) first. If not there, use your general Bali knowledge.
        FORMAT RULES (important — responses are sent via WhatsApp):
        - Use numbered lists (1. 2. 3.) for activity suggestions.
        - Use *bold* for activity names.
        - NEVER use markdown tables or HTML.
        - Keep each suggestion to 2–3 lines max.
        - Always end with a question like "Which of these sounds good to you?"
    """,
    "things-to-do-in-bali": """
        You are EasyBali’s Adventure & Exploration Guide for Bali.
        Mission: Provide a COMPLETE, COMPREHENSIVE guide to things to do in Bali. Cover ALL major categories — do not limit yourself to a short list.
        CONTENT: Include beaches & water sports, cultural landmarks & temples, adventure activities, local experiences, nightlife, day trips, family activities, wellness & spas, shopping, unique hidden gems. Give specific names, locations, and practical tips for each.
        FORMAT RULES:
        - Use numbered sections with *bold* section headers.
        - Under each section, list specific activities with 1–2 lines of detail each.
        - No tables. WhatsApp-friendly text only.
        - Be as thorough and informative as a professional travel guide.
    """,
    "plan-my-trip": """
        You are EasyBali — AI Travel Planner for Bali.
        Your style: proactive, enthusiastic, and structured. You ask smart questions to build a personalised itinerary.
        BEHAVIOUR:
        - When a new session starts, immediately ask the guest about their arrival date, trip duration, group size, and interests (adventure/culture/relaxation/food/nightlife). Ask ONE question at a time.
        - Once you have enough info, suggest a day-by-day itinerary with specific EasyBali services they can book.
        - Mention relevant promotions or discounts from context when available.
        - Always end each message with a clear next question or action.
        FORMAT: Use WhatsApp-friendly formatting — bold headers (*text*), numbered lists, no markdown tables.
    """,
    "event-calender": """
        You are EasyBali's Events & Culture Guide for Bali.
        Your job: provide a COMPLETE calendar of events, festivals, ceremonies, markets, beach parties, and cultural happenings in Bali.
        BEHAVIOUR:
        - Cover ALL areas: Seminyak, Canggu, Ubud, Uluwatu, Kuta, Nusa Dua, Sanur, Amed, Lovina.
        - Include recurring weekly events, monthly highlights, annual festivals, Hindu ceremonies, night markets, art shows, music events, beach clubs, and yoga/wellness retreats.
        - Include both tourist-facing events and authentic local ceremonies.
        - Give dates/timing, exact location, and what to expect for each. If exact current dates are unknown, state the typical recurring schedule clearly.
        - Be as comprehensive as a printed event guide — cover as many events as possible.
        FORMAT: Numbered list with *bold* event names, location, and timing. WhatsApp-friendly, no tables.
    """,
    "local-cuisine": """
        You are EasyBali's Local Food & Cuisine Guide for Bali.
        Mission: Provide a COMPLETE, COMPREHENSIVE guide to Balinese food, drinks, and dining for tourists. Cover everything — do not give a short list.
        CONTENT: Include traditional Balinese dishes, Indonesian staples, must-try street food, warung culture, fine dining spots, night markets, vegetarian/vegan options, drinks & local beverages, food safety tips, recommended restaurants by area (Seminyak, Canggu, Ubud, Kuta, Uluwatu), and unique local food experiences like cooking classes.
        FORMAT RULES:
        - Use numbered sections with *bold* section headers.
        - Under each section, list specific dishes or spots with 1–2 lines of detail.
        - No tables. WhatsApp-friendly text only.
        - Be as thorough and informative as a professional food travel guide.
    """,
    "currency-converter": """
        You are the Global Currency Assistant for tourists visiting Bali, Indonesia.

        CRITICAL RULE: The user's message will begin with [LIVE_RATES: ...] containing today's real exchange rates.
        You MUST use ONLY these injected rates for ALL calculations. Never use your training data for exchange rates — it is outdated.

        For every conversion:
        1. Extract the rate for the requested currency from the [LIVE_RATES] block.
        2. Calculate the exact converted amount using those rates.
        3. Show the result clearly (e.g., "100 INR = 18,250 IDR").
        4. Add one practical sentence (e.g., "Enough for a street-food meal in Seminyak.").

        You support ALL currencies — if a currency code appears in the [LIVE_RATES] block, you can convert it.
        Be friendly, concise, and helpful like a local Bali guide.
    """,
    "voice-translator": """
        You are the Global Language Translator. 
        Your mission is to translate exactly what the user asks across ANY language. 
        If they ask for Balinese or Indonesian, teach them the phrase with pronunciation. Otherwise, provide accurate translations for their requested language pair.
    """,
    "passport-submission": """
        Security Assistant. 
        Help with passport uploads. Guide to use the paperclip icon.
    """,
    "maintenance-issue": """
        You are the EASYBali Maintenance Concierge.
        Help villa guests report maintenance issues (broken AC, plumbing, electrical, pool, furniture etc.).
        Collect: type of issue, location in villa, urgency (low/medium/high), and any photos if available.
        Always reassure the guest the team will respond promptly. Keep responses short and professional.
    """,
    "general": """
        Premium concierge for Bali villa guests. 
        Professional, excited, high-end.
        You have been provided deep context from the Archive and Price Diff tabs. If a user asks about a service you cannot find in the active directory, check the Archive list provided in your context. If it's still not there, intelligently browse your own general knowledge to answer.
        
        CRITICAL RULES:
        - NEVER tell a user that a service is "booked" or that an "email has been sent" for booking.
        - If a user wants to book, guide them to use the interactive "Book" or "Options" buttons that appear in the chat.
        - If you don't see buttons yet, ask for their preferred date and time so the system can suggest options.
    """
}

class ConciergeAI:
    """
    CONTAINERIZED AI MODULE.
    Isolation Principle: Logic is separated from Routing.
    Local First Principle: Sheets -> RAG -> OpenAI.
    """
    def __init__(self, service_index: str = "ai-data"):
        self.service_index = service_index

    async def get_rag_context(self, query: str, chat_type: str = "general", villa_code: str = "WEB_VILLA_01") -> str:
        """Proxies to the unified RAG service"""
        return await rag_service.get_rag_context(query, chat_type, villa_code)

    def get_sheet_context(self) -> str:
        """INTERNAL DB FETCH (Priority 1)"""
        context = ""
        try:
            # 1. AI Data Sheet (Core context)
            if cache.get("ai_data_df") is not None and not cache["ai_data_df"].empty:
                context += "--- ACTIVE SERVICES ---\n"
                # Use all available active services for accuracy (usually < 200 items)
                for _, row in cache["ai_data_df"].iterrows():
                    context += f"- {row.get('Service Item')}: {row.get('Service Item Description')} Price: {row.get('Price (Service Item Button)')}\n"
            
            # 2. Archive Data Sheet (Deep context)
            if cache.get("archive_df") is not None and not cache["archive_df"].empty:
                context += "\n--- ARCHIVE DATA (Rentals & Legacy) ---\n"
                arch_lines = []
                # Increase visibility into archive for better rental identification
                for _, row in cache["archive_df"].head(300).iterrows():
                    valid = [f"{col}:{val}" for col, val in row.items() if pd.notna(val) and str(val).strip()]
                    if valid: arch_lines.append(" | ".join(valid))
                context += "\n".join(arch_lines) + "\n"

            # 3. Price Diff / Pricing Tiers
            for sheet_name, lbl in [("price_diff_df", "PRICE DIFF"), ("price_diff_sp_df", "PRICE DIFF SP")]:
                if cache.get(sheet_name) is not None and not cache[sheet_name].empty:
                    context += f"\n--- {lbl} ---\n"
                    lines = []
                    for _, row in cache[sheet_name].head(150).iterrows():
                        valid = [f"{col}:{val}" for col, val in row.items() if pd.notna(val) and str(val).strip()]
                        if valid: lines.append(" | ".join(valid))
                    context += "\n".join(lines) + "\n"
                    
            # 4. Platform Design
            if cache.get("platform_design_df") is not None and not cache["platform_design_df"].empty:
                context += "\n--- PLATFORM DESIGN ---\n"
                p_lines = []
                for _, row in cache["platform_design_df"].head(50).iterrows():
                    valid = [f"{col}:{val}" for col, val in row.items() if pd.notna(val) and str(val).strip()]
                    if valid: p_lines.append(" | ".join(valid))
                context += "\n".join(p_lines) + "\n"

        except Exception as e:
            logger.error(f"Sheet Context Compilation Error: {e}")
            
        # Ensure context doesn't explode in length (approx 12,000 chars safety cap)
        return context[:14000]

    async def process_query(self, query: str, user_id: str, chat_type: str, language: str, villa_code: str = "WEB_VILLA_01") -> Dict[str, Any]:
        """
        Process user query based on chat_type.
        Each chat type has an isolated path to prevent regression.
        Service booking detection ONLY runs for order-service modes.
        """
        try:
            print(f"DEBUG: Processing query='{query}' chat_type='{chat_type}' user='{user_id}'")
            history = get_conversation_history(user_id)
            conv = trim_history(history + [{"role": "user", "content": query}])
            formatted_history = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in conv])

            # ─── SERVICE BOOKING INTERCEPT (Dynamic Mapping) ────────────────────────
            # Intercept service requests across all chat types for consistency
            try:
                # Only run for modes that actually allow ordering
                if chat_type in ["general", "order-service", "plan-my-trip", "what-to-do", "things-to-do-in-bali", "local-cuisine"]:
                    service_check = await ai_menu_generator.intelligent_service_check(query)
                    if service_check.get("is_service_request") and service_check.get("we_offer_it"):
                        menu = await self._handle_booking(query, user_id, language, service_check, villa_code)
                        if menu:
                            return menu
            except Exception as e:
                logger.error(f"Service Check Error: {e}")

            # ─── PASSPORT SUBMISSION ───────────────────────────────────────────────
            if chat_type == "passport-submission":
                if query.lower() in ["hi", "hello", "hi there"]:
                    return self._passport_hi(user_id, language)
                # Let general AI handle follow-up, but keep persona focused
                resp = await self._call_openai(query, PERSONAS["passport-submission"], "", "", language, formatted_history, villa_code)
                save_message(user_id, "user", query)
                save_message(user_id, "assistant", resp)
                return {"response": resp}

            # ─── MAINTENANCE ISSUE ─────────────────────────────────────────────────
            if chat_type == "maintenance-issue":
                if query.lower() in ["hi", "hello", "hi there"]:
                    txt = (
                        "🛠️ Hi! I'm here to help log your maintenance issue.\n\n"
                        "Please describe the problem (e.g. broken AC, leaking tap, power outage). "
                        "I'll make sure the villa team is notified right away!"
                    )
                    save_message(user_id, "assistant", txt)
                    return {"response": txt}
                resp = await self._call_openai(query, PERSONAS["maintenance-issue"], "", "", language, formatted_history, villa_code)
                save_message(user_id, "user", query)
                save_message(user_id, "assistant", resp)
                # Save to issues DB so it's visible in Maintenance Issues dashboard
                _issue_kw = ["broken", "not working", "issue", "problem", "leaking", "leak",
                             "complain", "repair", "fix", "stuck", "noise", "smell", "dirty",
                             "ac", "wifi", "tv", "shower", "toilet", "door", "window", "lock",
                             "water", "electric", "power", "pool", "bed", "sofa", "fridge"]
                if len(query.strip()) > 10 and any(kw in query.lower() for kw in _issue_kw):
                    try:
                        from app.db.session import db as _issue_db
                        from datetime import datetime as _dt
                        await _issue_db["issues"].insert_one({
                            "sender_id": user_id,
                            "customer_id": None,
                            "villa_code": villa_code or "WEB_VILLA_01",
                            "description": query,
                            "media_type": "text",
                            "status": "open",
                            "source": "web",
                            "timestamp": _dt.utcnow()
                        })
                    except Exception as _ie:
                        logger.error(f"Failed to save web maintenance issue to DB: {_ie}")
                return {"response": resp}

            # ─── VOICE TRANSLATOR ──────────────────────────────────────────────────
            if chat_type == "voice-translator":
                if query.lower() in ["hi", "hello", "hi there", "start"]:
                    return self._voice_translator_hi(user_id, language)
                resp = await self._call_openai(query, PERSONAS["voice-translator"], "", "", language, formatted_history, villa_code)
                save_message(user_id, "user", query)
                save_message(user_id, "assistant", resp)
                return {"response": resp}

            # ─── CURRENCY CONVERTER ────────────────────────────────────────────────
            if chat_type == "currency-converter":
                resp = await self._call_openai(query, PERSONAS["currency-converter"], "", "", language, formatted_history, villa_code)
                save_message(user_id, "user", query)
                save_message(user_id, "assistant", resp)
                return {"response": resp}

            # ─── PLAN MY TRIP ──────────────────────────────────────────────────────
            if chat_type == "plan-my-trip":
                rag_ctx = await self.get_rag_context(query, chat_type, villa_code)
                resp = await self._call_openai(query, PERSONAS["plan-my-trip"], "", rag_ctx, language, formatted_history, villa_code)
                save_message(user_id, "user", query)
                save_message(user_id, "assistant", resp)
                return {"response": resp}

            # ─── WHAT TO DO / EVENT CALENDAR / LOCAL GUIDE ────────────────────────
            if chat_type in ["what-to-do", "local-cuisine", "things-to-do-in-bali", "event-calender"]:
                sheet_ctx = self.get_sheet_context()
                rag_ctx = await self.get_rag_context(query, chat_type, villa_code)
                persona = PERSONAS.get(chat_type, PERSONAS["what-to-do"])
                resp = await self._call_openai(query, persona, sheet_ctx, rag_ctx, language, formatted_history, villa_code)
                save_message(user_id, "user", query)
                save_message(user_id, "assistant", resp)
                return {"response": resp}

            # General fallback with RAG
            sheet_ctx = self.get_sheet_context()
            rag_ctx = await self.get_rag_context(query, chat_type, villa_code)
            persona = PERSONAS.get(chat_type, PERSONAS["general"])
            resp = await self._call_openai(query, persona, sheet_ctx, rag_ctx, language, formatted_history, villa_code)
            save_message(user_id, "user", query)
            save_message(user_id, "assistant", resp)
            return {"response": resp}

        except Exception as e:
            logger.error(f"Critical process_query Error: {e}")
            fallback_text = "Hi! I'm your EASYBali concierge. I'm currently experiencing some technical hiccups, but I'm still here to help with your villa stay. What can I do for you?"
            if language == "ID":
                fallback_text = "Halo! Saya pramutamu EASYBali Anda. Saat ini saya sedang mengalami sedikit masalah teknis, tetapi saya tetap di sini untuk membantu masa inap vila Anda. Apa yang bisa saya bantu?"
            return {"response": fallback_text}

    async def _call_openai(self, query: str, persona: str, sheet_ctx: str, rag_ctx: str, language: str, history: str, villa_code: str) -> str:
        """Centralised OpenAI call with a structured prompt."""
        from app.services.menu_services import get_villa_info_by_code
        villa_info = await get_villa_info_by_code(villa_code)
        villa_context = ""
        if villa_info:
             villa_context = f"VILLA INFO: Name: {villa_info.get('name')}, Location: {villa_info.get('location')}, Address: {villa_info.get('address')}"
             if villa_info.get('directions'):
                 villa_context += f", Directions: {villa_info.get('directions')}"
        
        prompt = f"""SYSTEM:
{villa_context}
You are assisting a guest at villa. Code: {villa_code}.

PERSONA:
{persona}

{"INTERNAL DB (use this first for prices/services):" + chr(10) + sheet_ctx if sheet_ctx else ""}

{"KNOWLEDGE BASE:" + chr(10) + rag_ctx if rag_ctx else ""}

RULES:
- Respond in language: {language}
- **GROUNDING RULE**: Use the provided "INTERNAL DB" and "KNOWLEDGE BASE" as your primary and mandatory sources of truth for specific services, prices, and house rules.
- **FALLBACK RULE**: If the required information is not found in the structured data above, only then use your general LLM reasoning to provide a helpful, culturally relevant answer. 
- **NO HALLUCINATION**: If structured data is missing, admit you don't have the exact price or detail but offer to help with general information.
- Be concise, helpful, and professional.
- Never say "Not Found" or expose technical errors to the user.
- Do NOT ask for information you already have.

CONVERSATION HISTORY:
{history}"""
        try:
            comp = await client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": query}],
                temperature=0.7,
                max_tokens=600
            )
            return comp.choices[0].message.content or "I'm here to help! How can I assist?"
        except Exception as e:
            logger.error(f"OpenAI call error: {e}")
            return "I'm having a moment of difficulty. I'm still here — please go ahead and ask me anything!"

    def _voice_translator_hi(self, user_id, lang):
        txt = "Halo! Saya mentor bahasa Anda. Mau belajar kata-kata keren dalam Bahasa Bali atau Indonesia hari ini? 🌴" if lang == "ID" else "Hi there! I'm your Language Mentor. Want to learn some cool Balinese or Indonesian phrases today? 🌴"
        save_message(user_id, "assistant", txt)
        return {"response": txt}

    def _passport_hi(self, user_id, lang):
        txt = "Pindah paspor Anda menggunakan ikon klip kertas 📎" if lang == "ID" else "Please upload your passport using the paperclip icon 📎"
        save_message(user_id, "assistant", txt)
        return {"response": txt}

    async def _handle_booking(self, query, user_id, lang, check, villa_code="WEB_VILLA_01"):
        try:
            matched_name = check.get("matched_service") or query
            intent = ai_menu_generator.detect_service_intent(matched_name)
            if intent:
                reqs = ai_menu_generator.extract_requirements(query)
                menu = await ai_menu_generator.generate_service_menu(intent["category"], intent["subcategory"], reqs, villa_code)
                if menu and "sections" in menu:
                    title = f"Pilihan untuk {intent['subcategory']}" if lang == "ID" else f"Options for {intent['subcategory']}"
                    table = {
                        "type": "service_selection", 
                        "title": title, 
                        "message": "I found these in our internal DB:", 
                        "options": menu["sections"][0]["rows"]
                    }
                    resp = f"SERVICES_DATA|{json.dumps(table)}"
                    save_message(user_id, "assistant", resp)
                    return {"response": resp}
        except Exception as e:
            logger.error(f"Handle Booking Error: {e}")
        return None

concierge_ai = ConciergeAI()
async def generate_response(query:str, user_id:str, chat_type:str="general", language:str="EN", villa_code:str="WEB_VILLA_01"):
    return await concierge_ai.process_query(query, user_id, chat_type, language, villa_code)

