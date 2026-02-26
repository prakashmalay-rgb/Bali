from fastapi import APIRouter, Depends, HTTPException, Form
from app.utils.auth import requires_role, create_access_token
from app.db.session import db
from datetime import datetime
import hashlib

router = APIRouter(prefix="/admin/users", tags=["Staff Management"])

user_collection = db["staff_users"]

@router.post("/login")
async def admin_login(email: str = Form(...), password: str = Form(...)):
    """
    Standard login for villa staff.
    """
    user = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Simple hash check
    hashed_pass = hashlib.sha256(password.encode()).hexdigest()
    if user["password"] != hashed_pass:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({
        "sub": email,
        "role": user["role"],
        "villa_codes": user.get("villa_codes", [])
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"]
    }

@router.post("/create", dependencies=[Depends(requires_role("admin"))])
async def create_staff(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("staff"),
    villas: str = Form("") # comma separated
):
    """
    Admin-only: Create new staff accounts.
    """
    existing_user = await user_collection.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed_pass = hashlib.sha256(password.encode()).hexdigest()
    
    new_user = {
        "email": email,
        "password": hashed_pass,
        "role": role,
        "villa_codes": villas.split(",") if villas else [],
        "created_at": datetime.utcnow()
    }
    
    await user_collection.insert_one(new_user)
    return {"status": "success", "message": f"User {email} created with role {role}"}

@router.get("/me")
async def get_my_info(user: dict = Depends(requires_role("read_only"))):
    return user
