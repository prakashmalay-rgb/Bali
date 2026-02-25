import json
import logging
from typing import Dict, Any, List
from fastapi import HTTPException
from app.settings.config import settings
from app.services.menu_services import cache
from app.services.openai_client import client
from app.utils.chat_memory import get_conversation_history, trim_history, save_message
from app.services.pinconeservice import get_index
from app.utils.navigation_rules import rules
from app.services.ai_menu_generator import ai_menu_generator

logger = logging.getLogger(__name__)

class ConciergeAI:
    def __init__(self, service_index: str = "ai-data"):
        self.service_index = service_index

    async def get_rag_context(self, query: str) -> str:
        """Retrieve context from Pinecone RAG."""
        try:
            index = get_index(self.service_index)
            if index is None:
                return ""

            embed_response = await client.embeddings.create(
                input=query,
                model="text-embedding-ada-002"
            )
            query_vector = embed_response.data[0].embedding
            
            query_response = index.query(vector=query_vector, top_k=3, include_metadata=True)
            matches = query_response.get("matches", [])
            return "\n\n".join([match["metadata"].get("text", "") for match in matches]) if matches else ""
        except Exception as e:
            logger.error(f"Error in RAG retrieval: {e}")
            return ""

    def get_sheet_context(self) -> str:
        """Extract fresh context from Google Sheets cache."""
        context = ""
        try:
            # 1. AI Data Sheet
            if cache.get("ai_data_df") is not None and not cache["ai_data_df"].empty:
                ai_df = cache["ai_data_df"]
                context += "REAL-TIME SERVICE DATA (AI Data Sheet):\n"
                for _, row in ai_df.head(25).iterrows():
                    context += f"- {row.get('Service Item')}: {row.get('Service Item Description')} price: {row.get('Price (Service Item Button)')}\n"

            # 2. General Services
            if cache.get("services_df") is not None:
                relevant_categories = ["Rental", "Discount & Promotions", "Villa Experiences", "Food and Beverage", "Transportation"]
                df = cache["services_df"]
                sample_df = df[df["Category"].isin(relevant_categories)].head(15)
                context += "\nOTHER CATEGORIES:\n"
                for _, row in sample_df.iterrows():
                    context += f"- {row.get('Service Item')} ({row.get('Category')}): price: {row.get('Price (Service Item Button)')}\n"
        except Exception as e:
            logger.error(f"Error extracting sheet context: {e}")
        return context

    async def process_query(self, query: str, user_id: str, chat_type: str = "general", language: str = "EN") -> Dict[str, Any]:
        """Core logic for generating AI responses."""
        
        # 1. Specialized Passport Submission logic
        if chat_type == "passport-submission" and query.lower() in ["hi", "hello", "hi there", "hey"]:
            return self._handle_passport_greeting(query, user_id, language)

        # 2. Service Intent Detection
        service_check = await ai_menu_generator.intelligent_service_check(query)
        if service_check.get("is_service_request") and service_check.get("we_offer_it"):
            menu_response = await self._handle_service_request(query, user_id, language, service_check)
            if menu_response:
                return menu_response

        # 3. General Conversation (RAG + Sheets)
        return await self._handle_general_conversation(query, user_id, chat_type, language)

    def _handle_passport_greeting(self, query: str, user_id: str, language: str) -> Dict[str, Any]:
        if language == "ID":
            response_text = (
                "Selamat datang di pusat **Pengiriman Paspor**! 🛂\n\n"
                "Untuk memastikan proses check-in yang lancar dan mematuhi peraturan setempat, kami memerlukan foto paspor Anda yang jelas.\n\n"
                "**Cara mengunggah:**\n"
                "1. Klik **ikon klip kertas** 📎 di sebelah input obrolan.\n"
                "2. Pilih gambar paspor Anda.\n"
                "3. Saya akan mengonfirmasi setelah diterima dengan aman!"
            )
        else:
            response_text = (
                "Welcome to the **Passport Submission** center! 🛂\n\n"
                "To ensure a smooth check-in and comply with local regulations, we need a clear photo of your passport.\n\n"
                "**How to upload:**\n"
                "1. Click the **paperclip icon** 📎 next to the chat input.\n"
                "2. Select your passport image.\n"
                "3. I'll confirm once it's securely received!"
            )
        save_message(user_id, "user", query)
        save_message(user_id, "assistant", response_text)
        return {"response": response_text}

    async def _handle_service_request(self, query: str, user_id: str, language: str, service_check: Dict) -> Optional[Dict]:
        matched_service = service_check.get("matched_service")
        intent = ai_menu_generator.detect_service_intent(matched_service or query)
        
        if intent:
            requirements = ai_menu_generator.extract_requirements(query)
            menu_data = await ai_menu_generator.generate_service_menu(
                intent["category"], 
                intent["subcategory"], 
                requirements
            )
            
            if menu_data and menu_data.get("sections") and menu_data["sections"][0].get("rows"):
                if language == "ID":
                    title = f"Pilihan Tersedia untuk {intent['subcategory']}"
                    message = f"Saya telah menemukan beberapa opsi untuk **{intent['subcategory']}**."
                else:
                    title = f"Available Options for {intent['subcategory']}"
                    message = f"I've found some options for **{intent['subcategory']}**."
                    
                table_response = {
                    "type": "service_selection",
                    "title": title,
                    "message": message,
                    "options": menu_data["sections"][0]["rows"]
                }
                response_text = f"SERVICES_DATA|{json.dumps(table_response)}"
                save_message(user_id, "user", query)
                save_message(user_id, "assistant", response_text)
                return {"response": response_text}
        return None

    async def _handle_general_conversation(self, query: str, user_id: str, chat_type: str, language: str) -> Dict[str, Any]:
        sheet_context = self.get_sheet_context()
        rag_context = await self.get_rag_context(query)
        full_context = f"{sheet_context}\n\n{rag_context}"

        chat_history = get_conversation_history(user_id)
        conversation = trim_history(chat_history + [{"role": "user", "content": query}])

        system_prompt = f"""
            You are **EASYbali AI**, a premium concierge assistant for villa guests in Bali.
            KNOWLEDGE BASE:
            {full_context if full_context.strip() else "Focus on general Bali knowledge but maintain EASYBali luxury standards."}

            STRICT INSTRUCTIONS:
            1. LANGUAGE: {language}.
            2. DATA: Prioritize KNOWLEDGE BASE for prices/discounts.
            3. RENTALS: Specifically check for car/bike rental keywords.
            4. BOOKING: Follow these rules: {rules}
            5. TONE: Professional & High-end.
            6. CHAT TYPE: {chat_type}
            
            History: {conversation}
        """

        try:
            completion = await client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.7
            )
            response = completion.choices[0].message.content
            save_message(user_id, "user", query)
            save_message(user_id, "assistant", response)
            return {"response": response}
        except Exception as e:
            logger.error(f"OpenAI Error: {e}")
            raise HTTPException(status_code=500, detail="The concierge is momentarily unavailable. Please try again!")

# Singleton instance
concierge_ai = ConciergeAI()

async def generate_response(query: str, user_id: str, chat_type: str = "general", language: str = "EN"):
    """Main entry point for chatbot responses."""
    try:
        return await concierge_ai.process_query(query, user_id, chat_type, language)
    except Exception as e:
        logger.error(f"Unhandled error in generate_response: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Something went wrong in the AI pipeline.")
