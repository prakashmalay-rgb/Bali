from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging

from app.services.analytics_service import (
    get_villa_performance,
    get_service_analytics,
    get_revenue_analytics,
    get_guest_analytics,
    get_promo_analytics
)
from app.utils.auth import requires_role

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)

@router.get("/villa-performance")
async def get_villa_performance_endpoint(
    villa_code: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(requires_role("staff"))
):
    """
    Get villa performance metrics (Staff+)
    """
    try:
        performance = await get_villa_performance(villa_code, days)
        
        return {
            "success": True,
            "period_days": days,
            "villa_filter": villa_code,
            "data": performance
        }
        
    except Exception as e:
        logger.error(f"Failed to get villa performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/service-analytics")
async def get_service_analytics_endpoint(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(requires_role("staff"))
):
    """
    Get service performance analytics (Staff+)
    """
    try:
        analytics = await get_service_analytics(days)
        
        return {
            "success": True,
            "period_days": days,
            "data": analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get service analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/revenue")
async def get_revenue_analytics_endpoint(
    days: int = Query(30, ge=1, le=365),
    group_by: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user: dict = Depends(requires_role("admin"))
):
    """
    Get revenue analytics (Admin only)
    """
    try:
        revenue = await get_revenue_analytics(days, group_by)
        
        return {
            "success": True,
            "period_days": days,
            "group_by": group_by,
            "data": revenue
        }
        
    except Exception as e:
        logger.error(f"Failed to get revenue analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/guest-analytics")
async def get_guest_analytics_endpoint(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(requires_role("admin"))
):
    """
    Get guest analytics (Admin only)
    """
    try:
        analytics = await get_guest_analytics(days)
        
        return {
            "success": True,
            "period_days": days,
            "data": analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get guest analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/promo-analytics")
async def get_promo_analytics_endpoint(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(requires_role("admin"))
):
    """
    Get promo code usage analytics (Admin only)
    """
    try:
        analytics = await get_promo_analytics(days)
        
        return {
            "success": True,
            "period_days": days,
            "data": analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get promo analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/dashboard")
async def get_analytics_dashboard(
    days: int = Query(30, ge=1, le=365),
    villa_code: Optional[str] = Query(None),
    current_user: dict = Depends(requires_role("staff"))
):
    """
    Get comprehensive analytics dashboard (Staff+)
    """
    try:
        # Get all analytics data
        villa_performance = await get_villa_performance(villa_code, days)
        service_analytics = await get_service_analytics(days)
        guest_analytics = await get_guest_analytics(days)
        
        # Revenue analytics (admin only)
        revenue_analytics = []
        if current_user.get("role") == "admin":
            revenue_analytics = await get_revenue_analytics(days, "daily")
            promo_analytics = await get_promo_analytics(days)
        else:
            promo_analytics = []
        
        # Calculate summary metrics
        total_revenue = sum(villa.get("total_revenue", 0) for villa in villa_performance)
        total_bookings = sum(villa.get("total_bookings", 0) for villa in villa_performance)
        total_completed = sum(villa.get("completed_bookings", 0) for villa in villa_performance)
        
        overall_completion_rate = (total_completed / total_bookings * 100) if total_bookings > 0 else 0
        
        return {
            "success": True,
            "period_days": days,
            "villa_filter": villa_code,
            "summary": {
                "total_revenue": total_revenue,
                "total_bookings": total_bookings,
                "completed_bookings": total_completed,
                "completion_rate": round(overall_completion_rate, 2),
                "total_guests": guest_analytics.get("total_guest_count", 0),
                "new_guests": guest_analytics.get("new_guest_count", 0),
                "returning_guests": guest_analytics.get("returning_guest_count", 0)
            },
            "villa_performance": villa_performance,
            "service_analytics": service_analytics,
            "guest_analytics": guest_analytics,
            "revenue_analytics": revenue_analytics,
            "promo_analytics": promo_analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/top-villas")
async def get_top_villas(
    metric: str = Query("revenue", regex="^(revenue|bookings|completion_rate)$"),
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(requires_role("staff"))
):
    """
    Get top performing villas by metric (Staff+)
    """
    try:
        performance = await get_villa_performance(days=days)
        
        # Sort by selected metric
        if metric == "revenue":
            sorted_villas = sorted(performance, key=lambda x: x.get("total_revenue", 0), reverse=True)
        elif metric == "bookings":
            sorted_villas = sorted(performance, key=lambda x: x.get("total_bookings", 0), reverse=True)
        else:  # completion_rate
            sorted_villas = sorted(performance, key=lambda x: x.get("completion_rate", 0), reverse=True)
        
        return {
            "success": True,
            "metric": metric,
            "period_days": days,
            "data": sorted_villas[:limit]
        }
        
    except Exception as e:
        logger.error(f"Failed to get top villas: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def analytics_health():
    """Health check for analytics service"""
    try:
        # Test database connection
        from app.db.session import db
        await db.command("ping")
        
        return {
            "status": "healthy",
            "service": "analytics",
            "collections": ["orders", "promo_codes"]
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
