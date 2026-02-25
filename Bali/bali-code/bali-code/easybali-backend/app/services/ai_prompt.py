from app.settings.config import settings
from fastapi import HTTPException
from app.services.menu_services import cache
from app.services.openai_client import client
from app.utils.chat_memory import get_conversation_history, trim_history, save_message
from app.services.pinconeservice import get_index
from app.utils.navigation_rules import rules

service_index="ai-data"


async def generate_response(query: str, user_id: str):
    index = get_index(service_index)
    chat_history = get_conversation_history(user_id)
    conversation = trim_history(chat_history + [{"role": "user", "content": query}])

    embed_response = await client.embeddings.create(
        input=query,
        model="text-embedding-ada-002"
    )
    query_vector = embed_response.data[0].embedding
    query_response = index.query(
        vector=query_vector,
        top_k=3,
        include_metadata=True
    )
    matches = query_response.get("matches", [])
    if not matches:
        context = ""
    else:
        context_chunks = [match["metadata"].get("text", "") for match in matches]
        context = "\n\n".join(context_chunks)
    
    prompt = f"""
        You are **EASYbali AI**, a premium concierge assistant for villa guests in Bali.
        
        PRIMARY SOURCE OF TRUTH (Google Sheet Context):
        {context if context else "No direct data found for this specific query. Proceed with general knowledge but stay aligned with EASYBali services."}

        STRICT INSTRUCTIONS:
        1. PRIORITIZE Information: Always check the 'PRIMARY SOURCE OF TRUTH' first. If the answer is there, use it as the definitive answer.
        2. NO HALLUCINATION: If the context specifies details (like pricing or availability), do not contradict them.
        3. EXTERNAL KNOWLEDGE: Only use external knowledge if the information is completely missing from the 'PRIMARY SOURCE OF TRUTH'.
        4. TONE: Be professional, warm, and helpful, like a high-end luxury concierge.
        5. BOOKING RULES: If the guest wants to book, use these rules: {rules}
        
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
        )

        response = completion.choices[0].message.content
        save_message(user_id, "user", query)
        save_message(user_id, "assistant", response)

        return {"response": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")