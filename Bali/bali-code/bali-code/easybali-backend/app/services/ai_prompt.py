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


async def generate_response(query: str, user_id: str, chat_type: str = "general"):
    # 1. Handle specialized chat types
    if chat_type == "passport-submission":
        if query.lower() in ["hi", "hello", "hi there", "hey"]:
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
                table_response = {
                    "type": "service_selection",
                    "title": f"Available Options for {intent['subcategory']}",
                    "message": f"I've found some epic options for **{intent['subcategory']}**. Pick your favorite to start booking!",
                    "options": menu_data["sections"][0]["rows"]
                }
                response_text = f"SERVICES_DATA|{json.dumps(table_response)}"
                save_message(user_id, "user", query)
                save_message(user_id, "assistant", response_text)
                return {"response": response_text}

    # 3. Fallback to RAG + Dynamic Sheet Context
    # We'll pull some fresh data from the cache to ensure the AI knows about new promos/rentals
    sheet_context = ""
    if cache.get("services_df") is not None:
        # Get a small sample of categories and services to ground the AI
        relevant_categories = ["Rental", "Discount & Promotions", "Villa Experiences", "Food and Beverage", "Transportation"]
        df = cache["services_df"]
        sample_df = df[df["Category"].isin(relevant_categories)].head(30)
        sheet_context = "AVAILABLE SERVICES & PROMOS FROM GOOGLE SHEETS (REAL-TIME DATA):\n"
        for _, row in sample_df.iterrows():
            sheet_context += f"- {row.get('Service Item')} ({row.get('Category')}): {row.get('Service Item Description')} price: {row.get('Price (Service Item Button)')}\n"

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
        1. LOCALLY GROWN DATA: Prioritize the 'KNOWLEDGE BASE' for prices, discounts, and specific rental options.
        2. RENTALS & PROMOS: If the user asks for rentals (cars, bikes, gear) or discounts, check the context specifically for those keywords.
        3. PASSING THE MIC: If a user wants to book, refer to these rules: {rules}
        4. TONE: Professional, infectious excitement, high-end concierge.
        5. CURRENT CHAT TYPE: {chat_type}
        
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
