from fastapi import APIRouter, Depends, HTTPException, Form
from app.utils.auth import requires_role, create_access_token
from app.db.session import db
from datetime import datetime
from pydantic import BaseModel
import bcrypt

router = APIRouter(prefix="/admin", tags=["Staff Management"])

user_collection = db["staff_users"]

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def admin_login(data: LoginRequest):
    """
    Standard login for villa staff. Compatible with both email and username.
    """
    user = await user_collection.find_one({
        "$or": [
            {"email": data.username},
            {"username": data.username}
        ]
    })
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Direct bcrypt verification
    stored_password = user["password"]
    if not bcrypt.checkpw(data.password.encode('utf-8'), stored_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate JWT
    token = create_access_token({
        "sub": user.get("email") or user.get("username"),
        "role": user["role"],
        "villa_codes": user.get("villa_codes", ["*"])
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "user": {
            "id": str(user["_id"]),
            "username": user.get("username") or user.get("email"),
            "role": user["role"]
        }
    }

@router.post("/users/create", dependencies=[Depends(requires_role("admin"))])
async def create_staff(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("staff"),
    villas: str = Form("") # comma separated
):
    """
    Admin-only: Create new staff accounts.
    """
    existing_user = await user_collection.find_one({
        "$or": [{"email": email}, {"username": username}]
    })
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Generate bcrypt hash
    salt = bcrypt.gensalt()
    hashed_pass = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    new_user = {
        "username": username,
        "email": email,
        "password": hashed_pass,
        "role": role,
        "villa_codes": villas.split(",") if villas else [],
        "created_at": datetime.utcnow()
    }
    
    await user_collection.insert_one(new_user)
    return {"status": "success", "message": f"User {username} created as {role}"}

@router.get("/users/me")
async def get_my_info(user: dict = Depends(requires_role("read_only"))):
    return user
