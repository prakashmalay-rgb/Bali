import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class PaymentInfo(BaseModel):
    xendit_invoice_id: Optional[str] = None
    payment_url: Optional[str] = None
    external_id: Optional[str] = None
    payment_status: str = "unpaid"
    payment_method: Optional[str] = None
    paid_at: Optional[datetime.datetime] = None
    paid_amount: Optional[Any] = None
    currency: str = "IDR"
    distribution_data: Optional[Dict[str, Any]] = None
    expired_at: Optional[datetime.datetime] = None
    failed_at: Optional[datetime.datetime] = None
    failure_reason: Optional[str] = None
    
    class Config:
        extra = "allow"

class Order(BaseModel):
    sender_id: str
    order_number: str
    service_name: str
    date: Optional[datetime.datetime] = None
    time: Optional[str] = None
    price: Optional[str] = None
    confirmation: bool = False
    status: str = "pending"
    payment: PaymentInfo = Field(default_factory=PaymentInfo)
    service_provider_code: Optional[str] = None
    villa_code: Optional[str] = None
    promo_code: Optional[str] = None
    discount_amount: float = 0.0
    original_price: Optional[str] = None
    
    # Provider Acceptance and Tracking
    confirmed_by_provider: Optional[str] = None
    confirmed_at: Optional[datetime.datetime] = None
    assigned_provider: Optional[str] = None
    provider_confirmed_at: Optional[datetime.datetime] = None
    provider_responses: Optional[List[Dict[str, Any]]] = None
    service_details: Optional[Dict[str, Any]] = None
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    class Config:
        extra = "allow"

class WebOrder(BaseModel):
    service_name: str
    name: str
    date: Optional[datetime.datetime] = None
    time: Optional[str] = None
    price: Optional[str] = None
    no_of_person: Optional[str] = None
    phone_number: Optional[str] = None
    confirmation: bool = False
    payment: PaymentInfo = Field(default_factory=PaymentInfo)
    
    class Config:
        extra = "allow"