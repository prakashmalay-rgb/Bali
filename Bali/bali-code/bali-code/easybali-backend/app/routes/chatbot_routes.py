from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas.ai_response import ChatbotResponse
from app.models.chatbot_models import ChatRequest
from app.services.ai_prompt import generate_response
from app.utils.bucket import upload_to_s3
from app.db.session import passport_collection, order_collection
from app.models.order_summary import Order, PaymentInfo
from app.services.payment_service import create_xendit_payment_with_distribution, update_order_with_payment_info, clean_price_string
from app.services.order_summary import get_next_order_id, save_order_to_db
from app.services.menu_services import cache
from app.services.promo_service import validate_promo_code, increment_promo_usage
from app.services.google_sheets_service import get_service_by_name, get_services_by_category, get_categories
from app.routes.service_inquiry import create_service_inquiry, notify_service_providers
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
    promo_code: Optional[str] = None

@router.post("/generate-response", response_model=ChatbotResponse)
async def generate_chatbot_response(request: ChatRequest, user_id: str):
    query = request.query
    chat_type = request.chat_type
    language = request.language
    villa_code = request.villa_code if hasattr(request, "villa_code") else "WEB_VILLA_01"
    return await generate_response(query, user_id, chat_type, language, villa_code)

@router.post("/services/categories")
async def get_service_categories_chat():
    """Get all available service categories for chatbot"""
    try:
        categories = await get_categories()
        return {
            "success": True,
            "categories": categories
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "categories": []
        }

@router.post("/services/list")
async def list_services_chat(request: dict):
    """List services with optional filtering for chatbot"""
    try:
        category = request.get('category')
        subcategory = request.get('subcategory')
        
        if category and subcategory:
            services = await get_services_by_category(category)
            services = [s for s in services if s['subcategory'].lower() == subcategory.lower()]
        elif category:
            services = await get_services_by_category(category)
        else:
            from app.services.google_sheets_service import get_all_services
            services = await get_all_services()
        
        return {
            "success": True,
            "services": services or [],
            "count": len(services) if services else 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "services": []
        }

@router.post("/create-booking-payment")
async def create_booking_payment(request: BookingRequest):
    try:
        # 1. Find service details from Google Sheets
        service = await get_service_by_name(request.title)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service '{request.title}' not found")
        
        # 2. Handle Promo Code
        final_price_val = clean_price_string(request.price)
        discount_amount = 0.0
        promo_msg = ""
        if request.promo_code:
            is_valid, final_amount, promo_msg = await validate_promo_code(request.promo_code, float(final_price_val))
            if is_valid:
                discount_amount = float(final_price_val) - final_amount
                final_price_val = int(final_amount)
                await increment_promo_usage(request.promo_code)
        
        # 3. Create Order
        order_number = await get_next_order_id()
        current_time = datetime.now()
        
        # Determine villa code and actual location zone
        req_villa_code = request.location_zone if request.location_zone else service.get('villa_code', 'WEB_VILLA_01')
        from app.services.menu_services import get_villa_location_by_code
        actual_location = await get_villa_location_by_code(req_villa_code) or "Bali"

        new_order = Order(
            sender_id=request.user_id,
            order_number=order_number,
            service_name=service['service_name'],
            price=str(final_price_val),
            original_price=request.price,
            promo_code=request.promo_code if discount_amount > 0 else None,
            discount_amount=discount_amount,
            confirmation=True,
            status="pending_payment",
            service_provider_code=service.get('service_provider_code', 'DEFAULT_SP'),
            villa_code=req_villa_code,
            created_at=current_time,
            updated_at=current_time
        )
        
        # 4. Save to DB
        await save_order_to_db(new_order.dict())

        # 5. Generate payment link immediately so the customer can pay right away
        payment_url = None
        try:
            payment_result = await create_xendit_payment_with_distribution(new_order)
            if payment_result.get('success'):
                await update_order_with_payment_info(order_number, payment_result)
                payment_url = payment_result.get('payment_url')
            else:
                import logging as _log
                _log.getLogger(__name__).warning(
                    f"Payment link creation failed for {order_number}: {payment_result.get('error')}"
                )
        except Exception as _pay_err:
            import logging as _log
            _log.getLogger(__name__).error(f"Exception creating payment for {order_number}: {_pay_err}")

        # 6. Notify Service Providers (they confirm availability; payment is already initiated)
        await notify_service_providers(service, new_order.dict())

        actual_location = await get_villa_location_by_code(req_villa_code) or "Bali"
        success_msg = (
            f"🎉 **Booking Request Received!**\n\n"
            f"**Order ID**: {order_number}\n"
            f"**Service**: {service['service_name']}\n"
            f"**Location**: {actual_location} Zone\n\n"
            f"💰 **Total**: IDR {final_price_val:,}"
        )
        if discount_amount > 0:
            success_msg += f"\n🎁 **Promo Applied**: {promo_msg}\n💸 **You Saved**: IDR {int(discount_amount):,}"

        if payment_url:
            response_text = (
                f"{success_msg}\n\n"
                f"✅ **Your secure payment link is ready!**\n\n"
                f"[**Click here to complete your payment**]({payment_url})\n\n"
                f"_Payment link expires in 24 hours. Once paid, you'll receive a confirmation with full booking details._"
            )
        else:
            response_text = (
                f"{success_msg}\n\n"
                f"⏳ **Next Steps**:\n"
                f"1. We've notified our service providers for your request.\n"
                f"2. Once a provider confirms their availability, we will send you a secure payment link immediately.\n"
                f"3. Complete the payment to finalize your booking.\n\n"
                f"📱 Contact support if you need assistance."
            )

        return {"response": response_text, "payment_url": payment_url, "order_number": order_number}
            
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