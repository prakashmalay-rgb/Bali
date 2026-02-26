from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
    chat_type: str = "general"
    language: str = "EN"
    villa_code: str = "WEB_VILLA_01"

class MenuRequest(BaseModel):
    type: str

class ServiceRequest(BaseModel):
    serviceitem_type: str