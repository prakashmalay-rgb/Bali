from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.db.session import db
from app.utils.auth import requires_role
from app.services.openai_client import client
from app.services.pinconeservice import get_index
import uuid

router = APIRouter(prefix="/faq-admin", tags=["FAQ Admin"])
faq_collection = db["villa_faqs"]

class FAQCreate(BaseModel):
    villa_code: str
    question: str
    answer: str

class FAQResponse(FAQCreate):
    id: str
    pinecone_id: str
    created_at: datetime
    updated_at: datetime

@router.post("/add", dependencies=[Depends(requires_role("staff"))])
async def add_custom_faq(faq: FAQCreate, user: dict = Depends(requires_role("staff"))):
    """
    Staff/Admin: Add a custom FAQ rule to a specific villa.
    Dual writes: 1) MongoDB for display, 2) Pinecone for Chatbot semantic search.
    """
    # Cross-villa isolation
    if user["role"] != "admin" and user.get("villa_code") != faq.villa_code:
        raise HTTPException(status_code=403, detail="You can only manage your own villa FAQs.")

    full_text = f"Q: {faq.question}\nA: {faq.answer}"
    point_id = str(uuid.uuid4())

    try:
        # Encode into Vector
        embed = await client.embeddings.create(input=full_text, model="text-embedding-ada-002")
        vector = embed.data[0].embedding
        
        # Upsert into Pinecone
        index = get_index("villa-faqs")
        if index:
            index.upsert(
                vectors=[{
                    "id": point_id,
                    "values": vector,
                    "metadata": {
                        "text": full_text,
                        "type": "custom_faq",
                        "villa_code": faq.villa_code
                    }
                }]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pinecone Vector Error: {str(e)}")

    # Save to MongoDB for Dashboard UI
    doc = {
        "villa_code": faq.villa_code,
        "question": faq.question,
        "answer": faq.answer,
        "pinecone_id": point_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    res = await faq_collection.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc.pop("_id", None)
    
    return {"message": "Custom FAQ successfully injected into Chatbot memory.", "faq": doc}

@router.get("/list/{villa_code}", dependencies=[Depends(requires_role("staff"))])
async def list_custom_faqs(villa_code: str, user: dict = Depends(requires_role("staff"))):
    """Staff/Admin: View all custom FAQs for the UI Dashboard."""
    if user["role"] != "admin" and user.get("villa_code") != villa_code:
        raise HTTPException(status_code=403, detail="You can only view your own villa FAQs.")
        
    cursor = faq_collection.find({"villa_code": villa_code}).sort("created_at", -1)
    faqs = await cursor.to_list(length=100)
    
    results = []
    for f in faqs:
        f["id"] = str(f["_id"])
        f.pop("_id", None)
        results.append(f)
        
    return {"faqs": results}

@router.delete("/delete/{faq_id}", dependencies=[Depends(requires_role("staff"))])
async def delete_faq(faq_id: str, villa_code: str, user: dict = Depends(requires_role("staff"))):
    """Staff/Admin: Delete a custom FAQ rule from MongoDB and Pinecone."""
    if user["role"] != "admin" and user.get("villa_code") != villa_code:
        raise HTTPException(status_code=403, detail="Forbidden")

    from bson.objectid import ObjectId
    try:
        doc = await faq_collection.find_one({"_id": ObjectId(faq_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="FAQ not found.")
            
        pinecone_id = doc.get("pinecone_id")
        
        # Delete from Pinecone
        if pinecone_id:
            index = get_index("villa-faqs")
            if index:
                index.delete(ids=[pinecone_id])
                
        # Delete from MongoDB
        await faq_collection.delete_one({"_id": ObjectId(faq_id)})
        return {"message": "FAQ successfully removed from Chatbot memory."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
