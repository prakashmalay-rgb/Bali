from fastapi import APIRouter, Depends, HTTPException, Form
from app.utils.auth import requires_role, create_access_token
from app.db.session import db
from datetime import datetime, timedelta
from pydantic import BaseModel
import bcrypt
import uuid
from app.utils.email_func import send_email

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


class ForgotPasswordRequest(BaseModel):
    email: str

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """
    Initiates the password reset flow by sending an email with a reset token.
    """
    user = await user_collection.find_one({"email": data.email})
    if not user:
        # We return success even if user doesn't exist for security purposes (don't leak emails)
        return {"status": "success", "message": "If that email exists, a reset link has been sent."}

    reset_token = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(hours=1)
    
    await user_collection.update_one(
        {"email": data.email},
        {"$set": {"reset_token": reset_token, "reset_token_expiry": expiry}}
    )

    from app.settings.config import settings
    frontend_url = getattr(settings, "WEB_BASE_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/admin/reset-password?token={reset_token}"
    
    html_content = f"""
    <h2>Password Reset Request</h2>
    <p>Hi {user.get('username', 'there')},</p>
    <p>We received a request to reset the password for your EasyBali Dashboard account.</p>
    <p>Click the link below to reset your password. This link will expire in 1 hour.</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>If you did not request a password reset, you can safely ignore this email.</p>
    <br>
    <p>Best Regards,</p>
    <p>The EasyBali Team</p>
    """
    
    await send_email(
        to_email=data.email,
        subject="EasyBali Dashboard - Password Reset",
        body=html_content,
        is_html=True
    )
    
    return {"status": "success", "message": "If that email exists, a reset link has been sent."}


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """
    Resets the password using a valid reset token.
    """
    user = await user_collection.find_one({
        "reset_token": data.token,
        "reset_token_expiry": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    salt = bcrypt.gensalt()
    hashed_pass = bcrypt.hashpw(data.new_password.encode('utf-8'), salt).decode('utf-8')
    
    await user_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password": hashed_pass},
            "$unset": {"reset_token": "", "reset_token_expiry": ""}
        }
    )
    
    return {"status": "success", "message": "Password successfully reset. You can now login."}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(requires_role("read_only"))
):
    """
    Allows a logged-in user to change their own password.
    """
    email_or_username = current_user.get("sub")
    user = await user_collection.find_one({
        "$or": [
            {"email": email_or_username},
            {"username": email_or_username}
        ]
    })
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    stored_password = user["password"]
    if not bcrypt.checkpw(data.current_password.encode('utf-8'), stored_password.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    salt = bcrypt.gensalt()
    hashed_pass = bcrypt.hashpw(data.new_password.encode('utf-8'), salt).decode('utf-8')
    
    await user_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": hashed_pass}}
    )
    
    return {"status": "success", "message": "Password updated successfully"}
