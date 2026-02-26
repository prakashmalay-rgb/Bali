from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.ai_response import ChatbotResponse
from app.models.chatbot_models import ChatRequest
from app.services.ai_prompt import generate_response
from app.utils.bucket import upload_to_s3
from app.db.session import passport_collection, order_collection
from app.models.order_summary import Order, PaymentInfo
from app.services.payment_service import create_xendit_payment_with_distribution, update_order_with_payment_info
from app.services.order_summary import get_next_order_id, save_order_to_db
from app.services.menu_services import cache
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import json

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

class BookingRequest(BaseModel):
    id: str
    title: str
    price: str
    user_id: str
    location_zone: Optional[str] = None

@router.post("/generate-response", response_model=ChatbotResponse)
async def generate_chatbot_response(request: ChatRequest, user_id: str):
    query = request.query
    chat_type = request.chat_type
    language = request.language
    return await generate_response(query, user_id, chat_type, language)

@router.post("/create-booking-payment")
async def create_booking_payment(request: BookingRequest):
    try:
        # 1. Find service details in cache
        service_name = request.title
        df = cache.get("services_df")
        if df is None:
            raise HTTPException(status_code=500, detail="Service data not loaded")
            
        match = df[df["Service Item"] == service_name]
        if match.empty:
            # Try partial match
            match = df[df["Service Item"].str.contains(service_name, case=False, na=False)]
            
        if match.empty:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
            
        row = match.iloc[0]
        
        # 2. Extract provider details
        sp_code = row.get("Service Provider Number") or "DEFAULT_SP"
        # Use location override if provided, otherwise default
        villa_code = request.location_zone if request.location_zone else "WEB_VILLA_01" 
        
        # 3. Create Order
        order_number = await get_next_order_id()
        current_time = datetime.now()
        
        new_order = Order(
            sender_id=request.user_id,
            order_number=order_number,
            service_name=service_name,
            price=request.price,
            confirmation=True,
            status="pending",
            service_provider_code=sp_code,
            villa_code=villa_code,
            created_at=current_time,
            updated_at=current_time
        )
        
        # 4. Save to DB
        await save_order_to_db(new_order.dict())
        
        # 5. Create Xendit Payment
        payment_result = await create_xendit_payment_with_distribution(new_order)
        
        if payment_result.get("success"):
            # 6. Update Order with payment info
            await update_order_with_payment_info(order_number, payment_result)
            
            payment_url = payment_result.get("payment_url")
            return {
                "response": f"Successfully generated your payment link for **{service_name}** at **{villa_code}**!\n\n[💳 Click here to pay via Xendit]({payment_url})\n\nYou will receive a confirmation once the payment is completed."
            }
        else:
            return {
                "response": f"Sorry, I encountered an error while generating the payment link: {payment_result.get('error')}. Please try again later."
            }
            
    except Exception as e:
        print(f"Error in create_booking_payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────
# CONTAINERIZED: Booking Cancellation
# ──────────────────────────────────────────────────────────────
class CancelRequest(BaseModel):
    order_number: str
    reason: Optional[str] = "User cancelled"

@router.post("/cancel-booking")
async def cancel_booking(request: CancelRequest):
    from app.services.order_summary import cancel_order
    result = await cancel_order(request.order_number, request.reason)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# ──────────────────────────────────────────────────────────────
# CONTAINERIZED: Booking History
# ──────────────────────────────────────────────────────────────
@router.get("/booking-history/{user_id}")
async def booking_history(user_id: str, page: int = 1, limit: int = 20):
    from app.services.order_summary import get_booking_history
    return await get_booking_history(user_id, page, limit)

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

from app.services.openai_client import client

@router.post("/upload-audio")
async def upload_audio_file(file: UploadFile = File(...)):
    try:
        # Read the file bytes
        file_bytes = await file.read()
        
        # Whisper requires a file-like object with a filename (including extension)
        import io
        audio_file = io.BytesIO(file_bytes)
        audio_file.name = file.filename if file.filename else "audio.webm"
        
        # Call OpenAI Whisper transcription
        transcript = await client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="text"
        )
        
        return {"transcript": transcript}
    except Exception as e:
        print(f"Error in Whisper audio upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))