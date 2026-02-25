import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from app.settings.config import settings
from app.services.menu_services import cache
from app.services.openai_client import client
from app.utils.chat_memory import get_conversation_history, trim_history, save_message
from app.services.pinconeservice import get_index
from app.utils.navigation_rules import rules
from app.services.ai_menu_generator import ai_menu_generator

logger = logging.getLogger(__name__)

# Specialized System Personas for different Chat Types
PERSONAS = {
    "what-to-do": """
        You’re EasyBali, Bali’s most enthusiastic travel pal! 
        Vibe: Friendly, witty, local. 
        Mission: Suggest activities found in the INTERNAL DB (Services sheet). 
        If nothing is there, suggest something epic from general knowledge.
    """,
    "plan-my-trip": """
        You are EasyBali - AI Travel Planner. 
        Process: 1. Days? 2. Base? 3. Interests? 4. Budget?
        One question at a time. Be systematic.
    """,
    "currency-converter": """
        You are the Currency Assistant. 
        Help with IDR conversions. Use clear numbers. 
        Current rate is roughly 1 USD = 15,500 IDR (mention this is an estimate).
    """,
    "voice-translator": """
        You are the Language Mentor. 
        Teach cool Balinese/Indonesian words. 
        Format: "Word [Pronunciation] - Meaning". 
        Example: "Suksma [Sook-sma] - Thank you".
    """,
    "things-to-do-in-bali": """
        You are the Activity Expert. 
        Focus on adrenaline, culture, and nature. 
        MISSION: Search the 'things-to-do' index first.
    """,
    "passport-submission": """
        Security Assistant. 
        Help with passport uploads. Guide to use the paperclip icon.
    """,
    "general": """
        Premium concierge for Bali villa guests. 
        Professional, excited, high-end.
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

    async def get_rag_context(self, query: str, chat_type: str = "general") -> str:
        try:
            index_name = "things-to-do-in-bali" if chat_type == "things-to-do-in-bali" else self.service_index
            index = get_index(index_name)
            if index is None: return ""

            embed = await client.embeddings.create(input=query, model="text-embedding-ada-002")
            res = index.query(vector=embed.data[0].embedding, top_k=3, include_metadata=True)
            return "\n\n".join([m["metadata"].get("text", "") for m in res.get("matches", [])])
        except Exception as e:
            logger.error(f"RAG Error: {e}")
            return ""

    def get_sheet_context(self) -> str:
        """INTERNAL DB FETCH (Priority 1)"""
        context = ""
        try:
            # 1. AI Data Sheet
            if cache.get("ai_data_df") is not None and not cache["ai_data_df"].empty:
                context += "INTERNAL DB SERVICES:\n"
                for _, row in cache["ai_data_df"].head(30).iterrows():
                    context += f"- {row.get('Service Item')}: {row.get('Service Item Description')} Price: {row.get('Price (Service Item Button)')}\n"
        except: pass
        return context

    async def process_query(self, query: str, user_id: str, chat_type: str, language: str) -> Dict[str, Any]:
        """Process user query with local-first priority and RAG fallback."""
        try:
            # Handle Greetings for specific types
            if chat_type == "passport-submission" and query.lower() in ["hi", "hello", "hi there"]:
                return self._passport_hi(user_id, language)

            # Service / Booking Check
            try:
                service_check = await ai_menu_generator.intelligent_service_check(query)
                if service_check.get("is_service_request") and service_check.get("we_offer_it"):
                    menu = await self._handle_booking(query, user_id, language, service_check)
                    if menu: return menu
            except Exception as e:
                logger.error(f"Service Check Error: {e}")
                # Continue to general AI if service check fails

            # General Logic - Fetch Context
            sheet_ctx = self.get_sheet_context()
            rag_ctx = await self.get_rag_context(query, chat_type)
            
            history = get_conversation_history(user_id)
            conv = trim_history(history + [{"role": "user", "content": query}])
            
            # Format history for prompt
            formatted_history = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in conv])
            
            system = f"""
                PERSONA: {PERSONAS.get(chat_type, PERSONAS['general'])}
                
                INTERNAL DB (PRIORITY): 
                {sheet_ctx if sheet_ctx else "No internal sheet data."}
                
                EXTERNAL KNOWLEDGE: 
                {rag_ctx if rag_ctx else "Use general knowledge."}
                
                RULES:
                1. Language: {language}
                2. Local First: Use INTERNAL DB for any service/price question.
                3. Voice Friendly: Keep responses under 3 sentences for better text-to-speech.
                4. Rules of Villa: {rules}
                
                CONVERSATION HISTORY:
                {formatted_history}
            """

            try:
                comp = await client.chat.completions.create(
                    model=settings.OPENAI_MODEL_NAME,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": query}],
                    temperature=0.7,
                    max_tokens=500
                )
                resp = comp.choices[0].message.content or "I'm here to help! How can I assist you today?"
            except Exception as ai_err:
                logger.error(f"OpenAI Completion Error: {ai_err}")
                resp = "I'm sorry, I'm having a bit of trouble connecting to my brain. How can I help you today? (Fallback)"

            save_message(user_id, "user", query)
            save_message(user_id, "assistant", resp)
            return {"response": resp}

        except Exception as e:
            logger.error(f"Critical process_query Error: {e}")
            fallback_text = "Hi! I'm your EASYBali concierge. I'm currently experiencing some technical hiccups, but I'm still here to help with your villa stay. What can I do for you?"
            if language == "ID":
                fallback_text = "Halo! Saya pramutamu EASYBali Anda. Saat ini saya sedang mengalami sedikit masalah teknis, tetapi saya tetap di sini untuk membantu masa inap vila Anda. Apa yang bisa saya bantu?"
            return {"response": fallback_text}

    def _passport_hi(self, user_id, lang):
        txt = "Pindah paspor Anda menggunakan ikon klip kertas \ud83d\udcce" if lang == "ID" else "Please upload your passport using the paperclip icon \ud83d\udcce"
        save_message(user_id, "assistant", txt)
        return {"response": txt}

    async def _handle_booking(self, query, user_id, lang, check):
        try:
            matched_name = check.get("matched_service") or query
            intent = ai_menu_generator.detect_service_intent(matched_name)
            if intent:
                reqs = ai_menu_generator.extract_requirements(query)
                menu = await ai_menu_generator.generate_service_menu(intent["category"], intent["subcategory"], reqs)
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
async def generate_response(query:str, user_id:str, chat_type:str="general", language:str="EN"):
    return await concierge_ai.process_query(query, user_id, chat_type, language)

