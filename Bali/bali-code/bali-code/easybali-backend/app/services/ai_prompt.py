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
        Help the guest plan their perfect trip in Bali. 
        Recommend activities, provide itineraries, and mention any available discounts or promotions (e.g. promo codes).
    """,
    "currency-converter": """
        You are the Global Currency Assistant. 
        Accurately convert ANY global currency provided by the user (USD, EUR, AUD, GBP, SGD, etc.) into Indonesian Rupiah (IDR) and vice versa.
        Use up-to-date realistic market estimates for conversions and state clearly amounts.
    """,
    "voice-translator": """
        You are the Global Language Translator. 
        Your mission is to translate exactly what the user asks across ANY language. 
        If they ask for Balinese or Indonesian, teach them the phrase with pronunciation. Otherwise, provide accurate translations for their requested language pair.
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

    async def get_rag_context(self, query: str, chat_type: str = "general", villa_code: str = "WEB_VILLA_01") -> str:
        try:
            # Query specific indexes, falling back to villa-faqs for general questions
            if chat_type == "things-to-do-in-bali":
                index_name = "things-to-do-in-bali"
            elif chat_type == "local-cuisine":
                index_name = "local-cuisine"
            else:
                index_name = "villa-faqs" # Primary fallback for general queries/house rules
                
            index = get_index(index_name)
            if index is None: return ""

            embed = await client.embeddings.create(input=query, model="text-embedding-ada-002")
            
            # Filter matches by villa_code if provided (Isolation Principle)
            filter_dict = {"villa_code": villa_code} if index_name == "villa-faqs" else None
            
            res = index.query(
                vector=embed.data[0].embedding, 
                top_k=5, 
                include_metadata=True,
                filter=filter_dict
            )
            
            all_matches = res.get("matches", [])
            high_confidence = [m for m in all_matches if m.get("score", 0) > 0.75]
            matches = [m["metadata"].get("text", "") for m in high_confidence]
            
            # ── RAG Retrieval Accuracy Monitoring ──
            all_scores = [round(m.get("score", 0), 4) for m in all_matches]
            avg_score = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0
            logger.info(
                f"RAG Monitor [{index_name}] | query='{query[:80]}' | "
                f"total_hits={len(all_matches)} | above_threshold={len(high_confidence)} | "
                f"scores={all_scores} | avg_score={avg_score} | "
                f"verdict={'HIT' if matches else 'MISS → LLM fallback'}"
            )
            
            return "\n\n".join(matches) if matches else ""
                
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

    async def process_query(self, query: str, user_id: str, chat_type: str, language: str, villa_code: str = "WEB_VILLA_01") -> Dict[str, Any]:
        """Process user query with local-first priority and RAG fallback."""
        try:
            # Handle Greetings for specific types
            if chat_type == "passport-submission" and query.lower() in ["hi", "hello", "hi there"]:
                return self._passport_hi(user_id, language)
            
            if chat_type == "voice-translator" and query.lower() in ["hi", "hello", "hi there", "start"]:
                return self._voice_translator_hi(user_id, language)

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
            rag_ctx = await self.get_rag_context(query, chat_type, villa_code)
            
            history = get_conversation_history(user_id)
            conv = trim_history(history + [{"role": "user", "content": query}])
            
            # Format history for prompt
            formatted_history = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in conv])
            
            prompt = f"""
                SYSTEM:
                You are currently assisting a guest at villa: {villa_code}.
                
                PERSONA: {PERSONAS.get(chat_type, PERSONAS['general'])}
                
                INTERNAL DB (PRIORITY): 
                {sheet_ctx if sheet_ctx else "No internal sheet data."}
                
                EXTERNAL KNOWLEDGE (RAG VILLA FAQs for {villa_code}): 
                {rag_ctx if rag_ctx else "No specific context provided. You must fall back to your own LLM reasoning and internal general knowledge for this specific villa. Do not state that you lack context or are an AI."}
                
                RULES:
                1. Language: {language}
                2. Local First: Use INTERNAL DB for any service/price question.
                3. Accuracy: If unsure, prioritize mentioning what we HAVE (internal db) over speculating.
                4. Rules of Villa: {rules}
                5. LLM Fallback: If EXTERNAL KNOWLEDGE is empty, synthesize the best possible logical answer based on standard hospitality reasoning without hesitation for {villa_code}.
                
                CONVERSATION HISTORY:
                {formatted_history}
            """

            try:
                comp = await client.chat.completions.create(
                    model=settings.OPENAI_MODEL_NAME,
                    messages=[{"role": "system", "content": prompt}, {"role": "user", "content": query}],
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

    def _voice_translator_hi(self, user_id, lang):
        txt = "Halo! Saya mentor bahasa Anda. Mau belajar kata-kata keren dalam Bahasa Bali atau Indonesia hari ini? 🌴" if lang == "ID" else "Hi there! I'm your Language Mentor. Want to learn some cool Balinese or Indonesian phrases today? 🌴"
        save_message(user_id, "assistant", txt)
        return {"response": txt}

    def _passport_hi(self, user_id, lang):
        txt = "Pindah paspor Anda menggunakan ikon klip kertas 📎" if lang == "ID" else "Please upload your passport using the paperclip icon 📎"
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
async def generate_response(query:str, user_id:str, chat_type:str="general", language:str="EN", villa_code:str="WEB_VILLA_01"):
    return await concierge_ai.process_query(query, user_id, chat_type, language, villa_code)

