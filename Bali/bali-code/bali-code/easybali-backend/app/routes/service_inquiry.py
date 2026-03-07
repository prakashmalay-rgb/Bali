from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.services.google_sheets_service import (
    get_all_services,
    get_services_by_category,
    get_service_by_name,
    get_categories
)
from app.services.payment_service import create_xendit_payment_with_distribution
from app.models.order_summary import Order
from app.utils.auth import get_current_user
from app.db.session import order_collection

router = APIRouter(prefix="/services", tags=["Service Inquiry"])
logger = logging.getLogger(__name__)

@router.get("/categories")
async def get_service_categories():
    """Get all available service categories"""
    try:
        categories = await get_categories()
        return {
            "success": True,
            "categories": categories
        }
    except Exception as e:
        logger.error(f"Failed to get categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")

@router.get("/list")
async def list_services(
    category: Optional[str] = None,
    subcategory: Optional[str] = None
):
    """List services with optional filtering"""
    try:
        if category and subcategory:
            services = await get_services_by_category(category)
            services = [s for s in services if s['subcategory'].lower() == subcategory.lower()]
        elif category:
            services = await get_services_by_category(category)
        else:
            services = await get_all_services()
        
        return {
            "success": True,
            "services": services,
            "count": len(services)
        }
    except Exception as e:
        logger.error(f"Failed to list services: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch services")

@router.get("/{service_name}")
async def get_service_details(service_name: str):
    """Get detailed information about a specific service"""
    try:
        service = await get_service_by_name(service_name)
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return {
            "success": True,
            "service": service
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch service details")

@router.post("/inquire")
async def create_service_inquiry(
    inquiry_data: Dict[str, Any],
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Create a service inquiry and generate payment link"""
    try:
        # Validate required fields
        required_fields = ['service_name', 'date', 'time', 'sender_id']
        for field in required_fields:
            if field not in inquiry_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Get service details from Google Sheets
        service = await get_service_by_name(inquiry_data['service_name'])
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Create order object
        order_data = {
            "order_number": f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "service_name": service['service_name'],
            "price": service['price'],
            "villa_code": service.get('villa_code', 'DEFAULT'),
            "service_provider_code": service.get('service_provider_code', 'DEFAULT'),
            "sender_id": inquiry_data['sender_id'],
            "date": inquiry_data['date'],
            "time": inquiry_data['time'],
            "promo_code": inquiry_data.get('promo_code'),
            "status": "pending_payment",
            "service_details": service,
            "created_at": datetime.utcnow()
        }
        
        # Save order to database
        order = Order(**order_data)
        await order_collection.insert_one(order_data)
        
        # 5. Notify Service Providers ONLY (No payment link yet)
        await notify_service_providers(service, order_data)
        
        return {
            "success": True,
            "order": {
                "order_number": order_data["order_number"],
                "service_name": order_data["service_name"],
                "price": order_data["price"],
                "date": order_data["date"],
                "time": order_data["time"],
                "status": "pending_confirmation"
            },
            "message": "We have notified our service providers of your request. You will receive a secure payment link once a provider confirms their availability."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create service inquiry: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process inquiry")

async def notify_service_providers(service: Dict[str, Any], order_data: Dict[str, Any]):
    """Notify relevant service providers about new service request"""
    try:
        from app.utils.whatsapp_func import fetch_whatsapp_numbers, send_whatsapp_order_to_SP, send_whatsapp_message

        service_name = service.get('service_name', '')
        service_numbers = await fetch_whatsapp_numbers(service_name)

        # [TESTING]: Hardcoded test SP - Clarence (remove after testing is complete)
        test_sp_num = "6281999281660"
        if test_sp_num not in service_numbers:
            service_numbers.append(test_sp_num)

        # [MONITORING]: Send plain-text only — no Accept/Decline buttons to monitoring number
        monitoring_num = "919840705435"
        try:
            await send_whatsapp_message(
                monitoring_num,
                f"📊 [MONITOR] New order {order_data.get('order_number')} placed for {service_name}. Notifying {len(service_numbers)} SP(s): {service_numbers}"
            )
        except Exception as e:
            logger.error(f"Failed to send monitoring message: {e}")

        logger.info(f"🚀 [Web Chat] Notifying {len(service_numbers)} numbers for {service_name}: {service_numbers}")

        for num in service_numbers:
            try:
                await send_whatsapp_order_to_SP(num, order_data)
            except Exception as e:
                logger.error(f"Failed to notify provider {num}: {e}")

    except Exception as e:
        logger.error(f"Failed to notify service providers: {str(e)}")

async def get_service_providers_for_service(service_name: str) -> List[Dict[str, Any]]:
    """Get list of service providers for a specific service"""
    # This would typically query your database
    # For now, return mock data
    return [
        {
            "provider_id": "SP001",
            "name": "John Doe",
            "phone": "+628123456789",
            "services": ["Airport Transfer", "City Tour"],
            "available": True
        }
    ]

async def send_service_request_notification(
    provider: Dict[str, Any], 
    service: Dict[str, Any], 
    order_data: Dict[str, Any]
):
    """Send service request notification to provider"""
    try:
        from app.utils.whatsapp_func import send_whatsapp_message
        
        message = f"""🔔 NEW SERVICE REQUEST
        
Service: {service['service_name']}
Date: {order_data['date']}
Time: {order_data['time']}
Customer: {order_data['sender_id']}
Price: {service['price']}

Reply 'CONFIRM' to accept this request or 'DECLINE' to decline.
First provider to confirm gets the assignment!

Reply 'CONFIRM {order_data['order_number']}' to accept."""
        
        await send_whatsapp_message(provider['phone'], message)
        
    except Exception as e:
        logger.error(f"Failed to send notification to provider {provider['provider_id']}: {str(e)}")

@router.post("/provider-response")
async def handle_provider_response(response_data: Dict[str, Any]):
    """Handle service provider response (confirm/decline)"""
    try:
        order_number = response_data.get('order_number')
        provider_id = response_data.get('provider_id')
        response = response_data.get('response')  # 'confirm' or 'decline'
        
        if response.lower() == 'confirm':
            # Assign provider to order
            await order_collection.update_one(
                {"order_number": order_number},
                {"$set": {
                    "assigned_provider": provider_id,
                    "provider_confirmed_at": datetime.utcnow(),
                    "status": "provider_confirmed"
                }}
            )
            
            # Send payment link to customer
            await send_payment_link_to_customer(order_number)
            
            return {"success": True, "message": "Provider confirmed and payment link sent"}
        
        elif response.lower() == 'decline':
            # Log decline and try next provider
            await order_collection.update_one(
                {"order_number": order_number},
                {"$push": {
                    "provider_responses": {
                        "provider_id": provider_id,
                        "response": "declined",
                        "timestamp": datetime.utcnow()
                    }
                }}
            )
            
            return {"success": True, "message": "Provider declined, notifying next provider"}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid response")
            
    except Exception as e:
        logger.error(f"Failed to handle provider response: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process response")

async def send_payment_link_to_customer(order_number: str):
    """Send payment link to customer"""
    try:
        # Get order with payment details
        order = await order_collection.find_one({"order_number": order_number})
        if not order:
            return
        
        from app.utils.whatsapp_func import send_whatsapp_message
        
        message = f"""💳 PAYMENT LINK GENERATED
        
Order: {order['order_number']}
Service: {order['service_name']}
Amount: {order['price']}

Click here to complete payment:
{order.get('payment_url', 'Payment link will be sent shortly')}

⏰ Payment link expires in 24 hours
Reply 'PAY' if you need a new payment link."""
        
        await send_whatsapp_message(order['sender_id'], message)
        
    except Exception as e:
        logger.error(f"Failed to send payment link: {str(e)}")

@router.get("/inquiry-status/{order_number}")
async def get_inquiry_status(order_number: str):
    """Get status of a service inquiry"""
    try:
        order = await order_collection.find_one({"order_number": order_number})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "success": True,
            "order_number": order_number,
            "status": order.get('status'),
            "assigned_provider": order.get('assigned_provider'),
            "payment_url": order.get('payment_url'),
            "created_at": order.get('created_at')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get inquiry status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch status")
