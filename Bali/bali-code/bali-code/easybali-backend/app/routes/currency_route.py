from fastapi import APIRouter
from app.schemas.ai_response import ChatbotQuery
from fastapi import HTTPException
from app.services.currency_convertor import currency_ai



router = APIRouter(prefix="/currency-converter", tags=["Chatbot"])


@router.post("/chat")
async def chat_endpoint(request: ChatbotQuery, user_id: str):  
    try:
        user_query = request.query
        response = await currency_ai(user_id=user_id, query=user_query, language=request.language)
        
        return {"response": response,}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {e}")