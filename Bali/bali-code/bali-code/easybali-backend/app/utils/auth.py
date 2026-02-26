from fastapi import Security, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.settings.config import settings
from datetime import datetime
from functools import wraps
from typing import List

security = HTTPBearer()

SECRET_KEY = settings.OPENAI_API_KEY # Re-using key as secret for simplicity, ideally separate
ALGORITHM = "HS256"

# Roles definition
ROLES = {
    "admin": 3,
    "staff": 2,
    "read_only": 1
}

def create_access_token(data: dict):
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(auth.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def requires_role(required_role: str):
    """
    Decorator/Dependency to check for specific role access.
    """
    async def role_checker(user: dict = Depends(get_current_user)):
        user_role = user.get("role", "read_only")
        if ROLES.get(user_role, 0) < ROLES.get(required_role, 0):
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required role: {required_role}"
            )
        return user
    return role_checker
