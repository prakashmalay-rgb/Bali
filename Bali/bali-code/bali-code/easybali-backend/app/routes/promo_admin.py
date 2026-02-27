from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.db.session import db
from app.utils.auth import requires_role

router = APIRouter(prefix="/promos", tags=["Promo Admin"])
promo_collection = db["promo_codes"]

class PromoCreate(BaseModel):
    code: str
    type: str = Field(..., pattern="^(percentage|fixed)$")
    value: float = Field(..., gt=0)
    usage_limit: Optional[int] = None
    expiry: Optional[datetime] = None
    active: bool = True

class PromoResponse(PromoCreate):
    current_usage: int
    id: str

    class Config:
        populate_by_name = True

@router.post("/create", dependencies=[Depends(requires_role("admin"))])
async def create_promo(promo: PromoCreate):
    """Admin only: Create a new promo code."""
    code_upper = promo.code.upper().strip()
    
    # Check if exists
    existing = await promo_collection.find_one({"code": code_upper})
    if existing:
        raise HTTPException(status_code=400, detail="Promo code already exists.")
        
    doc = promo.dict()
    doc["code"] = code_upper
    doc["current_usage"] = 0
    doc["created_at"] = datetime.utcnow()
    
    res = await promo_collection.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc.pop("_id", None)
    return {"message": "Promo code created", "promo": doc}

@router.get("/list", dependencies=[Depends(requires_role("staff"))])
async def list_promos():
    """Staff/Admin: List all promo codes."""
    cursor = promo_collection.find().sort("created_at", -1)
    promos = await cursor.to_list(length=100)
    
    results = []
    for p in promos:
        p["id"] = str(p["_id"])
        p.pop("_id", None)
        results.append(p)
        
    return {"promos": results}

@router.put("/{code}/toggle", dependencies=[Depends(requires_role("admin"))])
async def toggle_promo_status(code: str):
    """Admin only: Toggle active status of a promo code."""
    code_upper = code.upper().strip()
    promo = await promo_collection.find_one({"code": code_upper})
    
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found.")
        
    new_status = not promo.get("active", True)
    await promo_collection.update_one(
        {"code": code_upper},
        {"$set": {"active": new_status}}
    )
    
    return {"message": f"Promo code status updated to {'Active' if new_status else 'Inactive'}", "active": new_status}
