from app.settings.config import settings
from fastapi import HTTPException
from app.services.menu_services import cache
from app.services.openai_client import client
from app.utils.chat_memory import get_conversation_history, trim_history, save_message
from app.services.pinconeservice import get_index
from app.utils.navigation_rules import rules
from app.services.ai_menu_generator import ai_menu_generator
import json

service_index="ai-data"


async def generate_response(query: str, user_id: str, chat_type: str = "general", language: str = "EN"):
    # 1. Handle specialized chat types
    if chat_type == "passport-submission":
        if query.lower() in ["hi", "hello", "hi there", "hey"]:
            if language == "ID":
                response_text = (
                    "Selamat datang di pusat **Pengiriman Paspor**! 🛂\n\n"
                    "Untuk memastikan proses check-in yang lancar dan mematuhi peraturan setempat, kami memerlukan foto paspor Anda yang jelas (halaman utama dengan foto dan detail Anda).\n\n"
                    "**Cara mengunggah:**\n"
                    "1. Klik **ikon klip kertas** 📎 di sebelah input obrolan.\n"
                    "2. Pilih gambar paspor Anda.\n"
                    "3. Saya akan mengonfirmasi setelah diterima dengan aman!\n\n"
                    "Apakah paspor Anda sudah siap?"
                )
            else:
                response_text = (
                    "Welcome to the **Passport Submission** center! 🛂\n\n"
                    "To ensure a smooth check-in and comply with local regulations, we need a clear photo of your passport (the main page with your photo and details).\n\n"
                    "**How to upload:**\n"
                    "1. Click the **paperclip icon** 📎 next to the chat input.\n"
                    "2. Select your passport image.\n"
                    "3. I'll confirm once it's securely received!\n\n"
                    "Do you have your passport ready?"
                )
            save_message(user_id, "user", query)
            save_message(user_id, "assistant", response_text)
            return {"response": response_text}

    # 2. Check if user is asking for a service (Rentals, Massages, etc.)
    service_check = await ai_menu_generator.intelligent_service_check(query)
    
    if service_check.get("is_service_request") and service_check.get("we_offer_it"):
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
                    message = f"Saya telah menemukan beberapa opsi epik untuk **{intent['subcategory']}**. Pilih favorit Anda untuk mulai memesan!"
                else:
                    title = f"Available Options for {intent['subcategory']}"
                    message = f"I've found some epic options for **{intent['subcategory']}**. Pick your favorite to start booking!"
                    
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

    # 3. Fallback to RAG + Dynamic Sheet Context
    # We'll pull some fresh data from the cache to ensure the AI knows about new promos/rentals
    sheet_context = ""
    # 3.1 Pull from specialized 'AI Data' sheet first
    if cache.get("ai_data_df") is not None and not cache["ai_data_df"].empty:
        ai_df = cache["ai_data_df"]
        # Convert top rows to a readable format for prompt
        sheet_context += "REAL-TIME SERVICE DATA (AI Data Sheet):\n"
        for _, row in ai_df.head(25).iterrows():
            sheet_context += f"- {row.get('Service Item')}: {row.get('Service Item Description')} price: {row.get('Price (Service Item Button)')}\n"

    # 3.2 Add general services for additional coverage
    if cache.get("services_df") is not None:
        relevant_categories = ["Rental", "Discount & Promotions", "Villa Experiences", "Food and Beverage", "Transportation"]
        df = cache["services_df"]
        sample_df = df[df["Category"].isin(relevant_categories)].head(15)
        sheet_context += "\nOTHER CATEGORIES:\n"
        for _, row in sample_df.iterrows():
            sheet_context += f"- {row.get('Service Item')} ({row.get('Category')}): price: {row.get('Price (Service Item Button)')}\n"

    index = get_index(service_index)
    chat_history = get_conversation_history(user_id)
    conversation = trim_history(chat_history + [{"role": "user", "content": query}])

    embed_response = await client.embeddings.create(
        input=query,
        model="text-embedding-ada-002"
    )
    query_vector = embed_response.data[0].embedding
    query_response = index.query(vector=query_vector, top_k=3, include_metadata=True)
    
    matches = query_response.get("matches", [])
    pinecone_context = "\n\n".join([match["metadata"].get("text", "") for match in matches]) if matches else ""
    
    full_context = f"{sheet_context}\n\n{pinecone_context}"

    prompt = f"""
        You are **EASYbali AI**, a premium concierge assistant for villa guests in Bali.
        
        KNOWLEDGE BASE (Google Sheets & Docs):
        {full_context if full_context.strip() else "No specific data found. Be helpful based on general Bali knowledge but focus on EASYBali standard of luxury."}

        STRICT INSTRUCTIONS:
        1. RESPONSE LANGUAGE: You MUST respond in the following language: {language}. If the language is ID, use Indonesian/Balinese style. If EN, use English.
        2. LOCALLY GROWN DATA: Prioritize the 'KNOWLEDGE BASE' for prices, discounts, and specific rental options.
        3. RENTALS & PROMOS: If the user asks for rentals (cars, bikes, gear) or discounts, check the context specifically for those keywords.
        4. PASSING THE MIC: If a user wants to book, refer to these rules: {rules}
        5. TONE: Professional, infectious excitement, high-end concierge.
        6. CURRENT CHAT TYPE: {chat_type}
        
        Conversation History:
        {conversation}
    """

    try:
        completion = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query},
            ],
            temperature=0.7
        )

        response = completion.choices[0].message.content
        save_message(user_id, "user", query)
        save_message(user_id, "assistant", response)
        return {"response": response}
    
    except Exception as e:
        print(f"Error in AI Pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"The concierge is momentarily unavailable. Please try again!")
