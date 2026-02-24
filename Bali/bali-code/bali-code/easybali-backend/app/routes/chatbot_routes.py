from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.ai_response import ChatbotResponse
from app.models.chatbot_models import ChatRequest
from app.services.ai_prompt import generate_response
from app.utils.bucket import upload_to_s3
from app.db.session import passport_collection
from datetime import datetime

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@router.post("/generate-response", response_model=ChatbotResponse)
async def generate_chatbot_response(request: ChatRequest, user_id: str):
    query = request.query
    return await generate_response(query, user_id)

@router.post("/upload-passport")
async def upload_passport_file(user_id: str = Form(...), file: UploadFile = File(...)):
    try:
        # Upload to AWS S3
        file_url = await upload_to_s3(file)
        
        # Save reference into MongoDB
        await passport_collection.insert_one({
            "user_id": user_id,
            "passport_url": file_url,
            "status": "pending_verification",
            "uploaded_at": datetime.utcnow()
        })
        
        # Respond back with AI context wrapper
        return {"response": f"Awesome! I've successfully received and securely stored your passport image: [View Document]({file_url})\n\nIs there anything else I can help you with today?"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))