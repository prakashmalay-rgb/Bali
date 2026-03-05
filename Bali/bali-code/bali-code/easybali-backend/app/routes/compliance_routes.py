from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from app.services.compliance_service import (
    compliance_service,
    get_compliance_logs,
    get_compliance_stats
)
from app.utils.auth import requires_role

router = APIRouter(prefix="/compliance", tags=["Compliance"])
logger = logging.getLogger(__name__)

@router.get("/logs")
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    compliance_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(requires_role("admin"))
):
    """
    Retrieve compliance logs with filtering (Admin only)
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        logs = await compliance_service.get_compliance_logs(
            limit=limit,
            offset=offset,
            compliance_type=compliance_type,
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "success": True,
            "logs": logs,
            "total": len(logs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve compliance logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats")
async def get_stats(current_user: dict = Depends(requires_role("admin"))):
    """
    Get compliance statistics for dashboard (Admin only)
    """
    try:
        stats = await compliance_service.get_compliance_stats()
        
        return {
            "success": True,
            "stats": stats,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve compliance stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/dashboard")
async def get_compliance_dashboard(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(requires_role("admin"))
):
    """
    Get comprehensive compliance dashboard data
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get logs for the specified period
        logs = await compliance_service.get_compliance_logs(
            limit=1000,
            offset=0,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get overall stats
        stats = await compliance_service.get_compliance_stats()
        
        # Calculate daily activity
        daily_activity = {}
        for log in logs:
            date = log.get("timestamp", "").split("T")[0]
            if date not in daily_activity:
                daily_activity[date] = 0
            daily_activity[date] += 1
        
        # Calculate type distribution
        type_distribution = {}
        for log in logs:
            log_type = log.get("compliance_type", "unknown")
            if log_type not in type_distribution:
                type_distribution[log_type] = 0
            type_distribution[log_type] += 1
        
        # Calculate severity distribution for security events
        severity_distribution = {}
        for log in logs:
            if log.get("compliance_type") == "security_event":
                severity = log.get("details", {}).get("severity", "unknown")
                if severity not in severity_distribution:
                    severity_distribution[severity] = 0
                severity_distribution[severity] += 1
        
        return {
            "success": True,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "total_events": len(logs),
                "unique_users": len(set(log.get("user_id") for log in logs if log.get("user_id"))),
                "daily_average": len(logs) / days if days > 0 else 0
            },
            "stats": stats,
            "daily_activity": daily_activity,
            "type_distribution": type_distribution,
            "severity_distribution": severity_distribution,
            "recent_events": logs[:10]  # Last 10 events
        }
        
    except Exception as e:
        logger.error(f"Failed to generate compliance dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/log-test")
async def test_logging(
    action: str = Query(...),
    details: Optional[dict] = None,
    current_user: dict = Depends(requires_role("admin"))
):
    """
    Test compliance logging (Admin only)
    """
    try:
        await compliance_service.log_admin_action(
            user_id=current_user.get("user_id"),
            action=action,
            target_resource="test",
            details=details or {}
        )
        
        return {
            "success": True,
            "message": f"Test log entry created for action: {action}"
        }
        
    except Exception as e:
        logger.error(f"Failed to create test log: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def compliance_health():
    """Health check for compliance service"""
    try:
        # Test database connection
        from app.db.session import db
        await db.command("ping")
        
        return {
            "status": "healthy",
            "service": "compliance_logging",
            "collection": compliance_service.COMPLIANCE_LOG_COLLECTION
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
