from fastapi import APIRouter, HTTPException
from app.schemas.ai_response import ChatbotQuery
from app.services.ai_prompt import generate_response

router = APIRouter(prefix="/plan-my-trip", tags=["Chatbot"])

@router.post("/chat")
async def chat_endpoint(request: ChatbotQuery, user_id: str):
    """
    Isolated Plan My Trip Chat.
    Uses centralized generate_response for Local-First data fetching.
    """
    user_query = request.query
    if not user_query:
        raise HTTPException(status_code=400, detail="No query provided.")
    
    # Use centralized module with specific chat_type
    return await generate_response(
        query=user_query, 
        user_id=user_id, 
        chat_type="plan-my-trip", 
        language=request.language
    )