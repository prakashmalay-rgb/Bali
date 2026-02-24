from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
import os
import bcrypt

router = APIRouter(prefix="/admin", tags=["Admin Authentication"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_for_easybali")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

class LoginRequest(BaseModel):
    username: str
    password: str

# In a real production scenario, use a proper DB collection for admins.
# For Milestone 1, we hardware the default Admin credentials mapped to the provided DB username.
ADMIN_USERNAME = "easybali_admin"
# The hash of "BaliVM2026!"
ADMIN_PASSWORD_HASH = bcrypt.hashpw("BaliVM2026!".encode('utf-8'), bcrypt.gensalt())

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login")
async def login(credentials: LoginRequest):
    if credentials.username != ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Check password
    if not bcrypt.checkpw(credentials.password.encode('utf-8'), ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Generate token
    token = create_access_token({"sub": credentials.username, "role": "admin"})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": credentials.username,
            "role": "Villa Manager"
        }
    }
