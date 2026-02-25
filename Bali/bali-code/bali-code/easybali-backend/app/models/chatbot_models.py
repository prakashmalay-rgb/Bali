from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
    chat_type: str = "general"

class MenuRequest(BaseModel):
    type: str

class ServiceRequest(BaseModel):
    serviceitem_type: str