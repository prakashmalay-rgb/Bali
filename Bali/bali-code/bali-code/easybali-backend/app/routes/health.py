from fastapi import APIRouter
from datetime import datetime
import asyncio

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "easybali-backend",
        "version": "2.0.0"
    }

@router.get("/health/ready")
async def readiness_check():
    """Readiness check - verifies database connectivity"""
    try:
        from app.db.session import db
        # Test database connection
        await db.command("ping")
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/health/live")
async def liveness_check():
    """Liveness check - basic service health"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
