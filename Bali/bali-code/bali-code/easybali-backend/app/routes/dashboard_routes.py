from fastapi import APIRouter, Depends, Query, Response
from app.db.session import db, order_collection, passport_collection, checkin_collection, inquiry_collection, issue_collection, feedback_collection
from app.utils.auth import requires_role, get_current_user
from typing import Dict, Any, Optional, List, Annotated
from datetime import datetime
from bson import ObjectId
import csv
import io

router = APIRouter(prefix="/dashboard-api", tags=["Dashboard"], dependencies=[Depends(requires_role("read_only"))])

@router.get("/stats")
async def get_dashboard_stats(user: Annotated[dict, Depends(requires_role("read_only"))]) -> Dict[str, Any]:
    try:
        # Check if user is restricted to specific villas
        villa_filter = {}
        if "*" not in user.get("villa_codes", ["*"]):
            villa_filter = {"villa_code": {"$in": user["villa_codes"]}}

        # Total bookings
        total_bookings = await order_collection.count_documents(villa_filter)
        
        # Active Guests - count of distinct sender_ids
        unique_guests = await order_collection.distinct("sender_id", villa_filter)
        active_guests = len(unique_guests)
        
        # Revenue - Sum of "payment.paid_amount" for PAID orders
        pipeline = [
            {"$match": {"status": "PAID"}},
            {"$match": villa_filter},
            {"$group": {"_id": None, "total_revenue": {"$sum": "$payment.paid_amount"}}}
        ]
        revenue_result = await order_collection.aggregate(pipeline).to_list(1)
        revenue = revenue_result[0]["total_revenue"] if revenue_result else 0
        
        # Pending Inquiries and Issues
        pending_inquiries = await inquiry_collection.count_documents({"intent": "support_request", **villa_filter})
        reported_issues = await issue_collection.count_documents({"status": "open", **villa_filter})

        # Recent activity slice
        o_short = await order_collection.find(villa_filter).sort("updated_at", -1).limit(5).to_list(5)
        inq_short = await inquiry_collection.find(villa_filter).sort("timestamp", -1).limit(5).to_list(5)
        iss_short = await issue_collection.find(villa_filter).sort("timestamp", -1).limit(5).to_list(5)
        
        combined_recent = []
        for o in o_short:
            combined_recent.append({
                "id": str(o["_id"]),
                "guest": f"Guest {str(o.get('sender_id', ''))[-4:]}",
                "action": f"Booked {o.get('service_name', 'Service')}",
                "time": (o.get("updated_at") or o.get("created_at")),
                "status": "confirmed" if o.get("status") == "PAID" else "pending"
            })
        for i in inq_short:
            combined_recent.append({
                "id": str(i["_id"]),
                "guest": f"Guest {str(i.get('sender_id', ''))[-4:]}",
                "action": "Messaged AI",
                "time": i.get("timestamp"),
                "status": "resolved"
            })
        for s in iss_short:
            combined_recent.append({
                "id": str(s["_id"]),
                "guest": f"Guest {str(s.get('sender_id', ''))[-4:]}",
                "action": "Reported Issue",
                "time": s.get("timestamp"),
                "status": "pending" if s.get("status") == "open" else "completed"
            })
            
        combined_recent.sort(key=lambda x: x["time"] if isinstance(x["time"], datetime) else datetime.utcnow(), reverse=True)
        for item in combined_recent:
            if isinstance(item["time"], datetime):
                item["time"] = item["time"].strftime("%H:%M %d/%m")
            else:
                item["time"] = "Recently"

        return {
            "success": True,
            "stats": {
                "activeGuests": active_guests,
                "totalBookings": total_bookings,
                "revenue": revenue,
                "pendingInquiries": pending_inquiries + reported_issues,
                "reportedIssues": reported_issues
            },
            "recentActivity": combined_recent[:5]
        }
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        return {
            "success": False,
            "stats": { "activeGuests": 0, "totalBookings": 0, "revenue": 0, "pendingInquiries": 0 },
            "recentActivity": []
        }

@router.get("/activity")
async def get_guest_activity(user: Annotated[dict, Depends(requires_role("read_only"))]) -> Dict[str, Any]:
    try:
        villa_filter = {}
        if "*" not in user.get("villa_codes", ["*"]):
            villa_filter = {"villa_code": {"$in": user["villa_codes"]}}
        recent_orders = await order_collection.find(villa_filter).sort("updated_at", -1).limit(20).to_list(20)
        recent_inquiries = await inquiry_collection.find(villa_filter).sort("timestamp", -1).limit(20).to_list(20)
        recent_issues = await issue_collection.find(villa_filter).sort("timestamp", -1).limit(20).to_list(20)
        activity_list = []
        for order in recent_orders:
            db_status = order.get("status", "pending")
            activity_list.append({
                "id": str(order.get("_id")),
                "type": "order",
                "guest_name": f"Guest {str(order.get('sender_id', ''))[-4:]}",
                "action": f"Paid for {order.get('service_name')}" if db_status == "PAID" else f"Requested {order.get('service_name')}",
                "service": order.get("service_name", "Service"),
                "amount": order.get("payment", {}).get("paid_amount", 0),
                "time": order.get("updated_at") or order.get("created_at") or datetime.utcnow(),
                "status": "completed" if db_status == "PAID" else "pending",
                "icon": "payment" if db_status == "PAID" else "request"
            })
        for inq in recent_inquiries:
            activity_list.append({
                "id": str(inq.get("_id")),
                "type": "inquiry",
                "guest_name": f"Guest {str(inq.get('sender_id', ''))[-4:]}",
                "action": "Messaged AI",
                "service": f"Topic: {inq.get('intent', 'General')}",
                "amount": 0,
                "time": inq.get("timestamp") or datetime.utcnow(),
                "status": "resolved",
                "icon": "info"
            })
        for issue in recent_issues:
            activity_list.append({
                "id": str(issue.get("_id")),
                "type": "issue",
                "guest_name": f"Guest {str(issue.get('sender_id', ''))[-4:]}",
                "action": "Reported Issue",
                "service": (issue.get("description", "Maintenance")[:30] + "...") if issue.get("description") else "Maintenance",
                "amount": 0,
                "time": issue.get("timestamp") or datetime.utcnow(),
                "status": "pending" if issue.get("status") == "open" else "completed",
                "icon": "request"
            })
        activity_list.sort(key=lambda x: x["time"] if isinstance(x["time"], datetime) else datetime.utcnow(), reverse=True)
        for act in activity_list:
            if isinstance(act["time"], datetime): act["time"] = act["time"].strftime("%Y-%m-%d %H:%M:%S")
            else: act["time"] = "Recently"
        return {"success": True, "activity": activity_list[:50]}
    except Exception as e:
        return {"success": False, "error": str(e), "activity": []}

@router.get("/activity/{item_type}/{item_id}")
async def get_activity_detail(item_type: str, item_id: str, _user: Annotated[dict, Depends(requires_role("read_only"))]) -> Dict[str, Any]:
    try:
        oid = ObjectId(item_id)
        if item_type == "issue":
            doc = await issue_collection.find_one({"_id": oid})
            if not doc:
                return {"success": False, "error": "Not found"}
            doc["_id"] = str(doc["_id"])
            if isinstance(doc.get("timestamp"), datetime): doc["timestamp"] = doc["timestamp"].isoformat()
            return {"success": True, "type": "issue", "data": doc}
        elif item_type == "inquiry":
            doc = await inquiry_collection.find_one({"_id": oid})
            if not doc:
                return {"success": False, "error": "Not found"}
            doc["_id"] = str(doc["_id"])
            if isinstance(doc.get("timestamp"), datetime): doc["timestamp"] = doc["timestamp"].isoformat()
            return {"success": True, "type": "inquiry", "data": doc}
        elif item_type == "order":
            doc = await order_collection.find_one({"_id": oid})
            if not doc:
                return {"success": False, "error": "Not found"}
            doc["_id"] = str(doc["_id"])
            for field in ("created_at", "updated_at"):
                if isinstance(doc.get(field), datetime): doc[field] = doc[field].isoformat()
            return {"success": True, "type": "order", "data": doc}
        else:
            return {"success": False, "error": "Unknown item type"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/chats")
async def get_concierge_chats() -> Dict[str, Any]:
    from app.utils.chat_memory import chat_memory
    try:
        chat_sessions = []
        for user_id, messages in chat_memory.items():
            chat_sessions.append({
                "guest_id": user_id,
                "guest_name": f"Guest {str(user_id)[-4:]}",
                "message_count": len(messages),
                "last_active": "Recently",
                "transcript": messages
            })
        return {"success": True, "sessions": chat_sessions}
    except Exception as e:
        return {"success": False, "error": str(e), "sessions": []}

@router.get("/passports")
async def get_passport_submissions() -> Dict[str, Any]:
    try:
        recent_passports = await passport_collection.find().sort("uploaded_at", -1).limit(50).to_list(50)
        from app.routes.passport_routes import get_presigned_url
        passport_list = []
        for passport in recent_passports:
            time_val = passport.get("uploaded_at")
            time_str = time_val.strftime("%Y-%m-%d %H:%M:%S") if hasattr(time_val, "strftime") else "Recently"
            user_id = str(passport.get("user_id", "Unknown"))
            s3_key_raw = passport.get("s3_key") or passport.get("passport_url", "")
            if s3_key_raw.startswith("http"):
                parsed_key = s3_key_raw.split(".amazonaws.com/")[-1]
            else:
                parsed_key = s3_key_raw
            secure_url = get_presigned_url(parsed_key) if parsed_key else passport.get("passport_url")
            passport_list.append({
                "id": str(passport.get("_id")),
                "guest_id": user_id,
                "guest_name": passport.get("guest_name", f"Guest {user_id[-4:]}"),
                "villa_code": passport.get("villa_code", "N/A"),
                "passport_url": secure_url,
                "status": passport.get("status", "pending_verification"),
                "source": passport.get("source", "whatsapp"),
                "time": time_str
            })
        return {"success": True, "passports": passport_list}
    except Exception as e:
        return {"success": False, "error": str(e), "passports": []}

@router.get("/checkins")
async def get_checkins() -> Dict[str, Any]:
    try:
        recent_checkins = await checkin_collection.find().sort("checkin_time", -1).limit(50).to_list(50)
        checkin_list = []
        for c in recent_checkins:
            time_val = c.get("checkin_time")
            checkout_val = c.get("estimated_checkout")
            checkin_list.append({
                "id": str(c.get("_id")),
                "guest_id": c.get("sender_id"),
                "villa_code": c.get("villa_code", "N/A"),
                "villa_name": c.get("villa_name", "N/A"),
                "status": c.get("status", "active"),
                "time": time_val.strftime("%Y-%m-%d %H:%M:%S") if hasattr(time_val, "strftime") else "Recently",
                "checkout_time": checkout_val.strftime("%Y-%m-%d %H:%M") if hasattr(checkout_val, "strftime") else "Pending",
                "keys_returned": c.get("keys_returned", False),
                "keys_returned_at": c.get("keys_returned_at").isoformat() if hasattr(c.get("keys_returned_at"), "isoformat") else None,
            })
        return {"success": True, "checkins": checkin_list}
    except Exception as e:
        return {"success": False, "error": str(e), "checkins": []}


@router.post("/checkins/{checkin_id}/keys-returned")
async def mark_keys_returned(
    checkin_id: str,
    user: Annotated[dict, Depends(requires_role("staff"))]
) -> Dict[str, Any]:
    """Staff confirms that keys have been returned at checkout."""
    try:
        doc = await checkin_collection.find_one({"_id": ObjectId(checkin_id)})
        if not doc:
            return {"success": False, "error": "Check-in not found"}
        if "*" not in user.get("villa_codes", ["*"]) and doc.get("villa_code") not in user["villa_codes"]:
            return {"success": False, "error": "Access denied"}
        await checkin_collection.update_one(
            {"_id": ObjectId(checkin_id)},
            {"$set": {
                "keys_returned": True,
                "keys_returned_at": datetime.utcnow(),
                "keys_returned_by": user.get("email", "staff"),
            }}
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/issues")
async def get_issues(user: Annotated[dict, Depends(get_current_user)]) -> Dict[str, Any]:
    try:
        villa_filter = {}
        if "*" not in user.get("villa_codes", ["*"]):
            villa_filter = {"villa_code": {"$in": user["villa_codes"]}}

        recent_issues = await issue_collection.find(villa_filter).sort("timestamp", -1).limit(50).to_list(50)
        issue_list = []
        for i in recent_issues:
            time_val = i.get("timestamp")
            issue_list.append({
                "id": str(i.get("_id")),
                "guest_id": i.get("sender_id"),
                "villa_code": i.get("villa_code", "N/A"),
                "description": i.get("description", ""),
                "media_type": i.get("media_type", "text"),
                "media_url": i.get("media_url"),
                "status": i.get("status", "open"),
                "source": i.get("source", "web"),
                "time": time_val.strftime("%Y-%m-%d %H:%M:%S") if hasattr(time_val, "strftime") else "Recently"
            })
        return {"success": True, "issues": issue_list}
    except Exception as e:
        return {"success": False, "error": str(e), "issues": []}

@router.get("/inquiries")
async def get_inquiries() -> Dict[str, Any]:
    try:
        recent_inquiries = await inquiry_collection.find().sort("timestamp", -1).limit(50).to_list(50)
        inquiry_list = []
        for i in recent_inquiries:
            time_val = i.get("timestamp")
            inquiry_list.append({
                "id": str(i.get("_id")),
                "guest_id": i.get("sender_id"),
                "villa_code": i.get("villa_code", "N/A"),
                "query": i.get("query", ""),
                "response": i.get("response", ""),
                "status": i.get("status", "responded"),
                "time": time_val.strftime("%Y-%m-%d %H:%M:%S") if hasattr(time_val, "strftime") else "Recently"
            })
        return {"success": True, "inquiries": inquiry_list}
    except Exception as e:
        return {"success": False, "error": str(e), "inquiries": []}

@router.get("/feedback")
async def get_feedback(user: Annotated[dict, Depends(requires_role("read_only"))]) -> Dict[str, Any]:
    try:
        villa_filter = {}
        if "*" not in user.get("villa_codes", ["*"]):
            villa_filter = {"villa_code": {"$in": user["villa_codes"]}}
        recent_feedback = await feedback_collection.find(villa_filter).sort("timestamp", -1).limit(100).to_list(100)
        feedback_list = []
        for f in recent_feedback:
            time_val = f.get("timestamp")
            feedback_list.append({
                "id": str(f.get("_id")),
                "guest_id": f.get("sender_id"),
                "villa_code": f.get("villa_code", "N/A"),
                "rating": f.get("rating"),
                "comment": f.get("comment", ""),
                "time": time_val.strftime("%Y-%m-%d %H:%M:%S") if hasattr(time_val, "strftime") else "Recently"
            })
        return {"success": True, "feedback": feedback_list}
    except Exception as e:
        return {"success": False, "error": str(e), "feedback": []}

@router.get("/bookings")
async def get_all_bookings(
    user: Annotated[dict, Depends(requires_role("read_only"))],
    status: Optional[str] = Query(None),
    villa: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
) -> Dict[str, Any]:
    try:
        query = {}
        # Multi-tenant filtering
        if "*" not in user.get("villa_codes", ["*"]):
            query["villa_code"] = {"$in": user["villa_codes"]}

        # Additional filters
        if status:
            query["status"] = status
        if villa:
            query["villa_code"] = villa
        if search:
            query["$or"] = [
                {"order_number": {"$regex": search, "$options": "i"}},
                {"sender_id": {"$regex": search, "$options": "i"}},
                {"service_name": {"$regex": search, "$options": "i"}},
            ]

        bookings = await order_collection.find(query).sort("created_at", -1).limit(100).to_list(100)
        formatted = []
        for b in bookings:
            formatted.append({
                "id": str(b["_id"]),
                "order_number": b.get("order_number"),
                "guest_id": b.get("sender_id"),
                "service": b.get("service_name"),
                "villa": b.get("villa_code", "N/A"),
                "amount": b.get("payment", {}).get("paid_amount", 0),
                "status": b.get("status", "pending"),
                "time": b.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if isinstance(b.get("created_at"), datetime) else "Recently"
            })
        return {"success": True, "bookings": formatted}
    except Exception as e:
        return {"success": False, "error": str(e), "bookings": []}


@router.get("/bookings/{booking_ref}")
async def get_booking_detail(
    booking_ref: str,
    user: Annotated[dict, Depends(requires_role("read_only"))]
) -> Dict[str, Any]:
    try:
        # Try by order_number first, then by ObjectId
        booking = await order_collection.find_one({"order_number": booking_ref})
        if not booking:
            try:
                booking = await order_collection.find_one({"_id": ObjectId(booking_ref)})
            except Exception:
                pass

        if not booking:
            return {"success": False, "error": "Booking not found"}

        # Multi-tenant check
        if "*" not in user.get("villa_codes", ["*"]):
            if booking.get("villa_code") not in user["villa_codes"]:
                return {"success": False, "error": "Access denied"}

        # Serialize ObjectId and datetimes
        booking["_id"] = str(booking["_id"])
        for field in ["created_at", "updated_at", "confirmed_at", "provider_confirmed_at"]:
            if field in booking and isinstance(booking[field], datetime):
                booking[field] = booking[field].isoformat()

        payment = booking.get("payment", {})
        for pfield in ["paid_at", "expired_at", "failed_at"]:
            if isinstance(payment.get(pfield), datetime):
                payment[pfield] = payment[pfield].isoformat()

        invoice = booking.get("invoice", {})
        if isinstance(invoice.get("generated_at"), datetime):
            invoice["generated_at"] = invoice["generated_at"].isoformat()

        return {"success": True, "booking": booking}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/bookings/{booking_ref}/invoice-url")
async def get_fresh_invoice_url(
    booking_ref: str,
    user: Annotated[dict, Depends(requires_role("read_only"))]
) -> Dict[str, Any]:
    """Generate a fresh pre-signed S3 URL for the invoice PDF (valid 1 hour)."""
    from app.routes.passport_routes import get_presigned_url

    booking = await order_collection.find_one({"order_number": booking_ref})
    if not booking:
        return {"success": False, "error": "Booking not found"}
    if "*" not in user.get("villa_codes", ["*"]) and booking.get("villa_code") not in user["villa_codes"]:
        return {"success": False, "error": "Access denied"}

    object_key = booking.get("invoice", {}).get("object_key", "")

    # Legacy records: derive object_key from the stored S3 URL
    if not object_key:
        stored_url = booking.get("invoice", {}).get("download_url", "")
        if stored_url:
            # URL format: https://<bucket>.s3.amazonaws.com/<key>?...
            # or https://s3.amazonaws.com/<bucket>/<key>?...
            from urllib.parse import urlparse
            parsed = urlparse(stored_url)
            path = parsed.path.lstrip("/")
            # If path starts with bucket name (path-style), strip it
            from app.settings.config import settings
            bucket = getattr(settings, "AWS_BUCKET_NAME", "easybali")
            if path.startswith(bucket + "/"):
                path = path[len(bucket) + 1:]
            object_key = path
        if not object_key:
            return {"success": False, "error": "No invoice found for this booking"}

    fresh_url = get_presigned_url(object_key, expiration=3600)
    return {"success": True, "url": fresh_url}


@router.put("/passports/{passport_id}/verify")
async def verify_passport(passport_id: str) -> Dict[str, Any]:
    from app.utils.whatsapp_func import send_whatsapp_message
    try:
        passport = await passport_collection.find_one({"_id": ObjectId(passport_id)})
        if not passport:
            return {"success": False, "error": "Passport submission not found"}
        await passport_collection.update_one(
            {"_id": ObjectId(passport_id)},
            {"$set": {"status": "verified", "verified_at": datetime.utcnow()}}
        )
        user_id = passport.get("user_id")
        if user_id:
            msg = (
                f"✅ *Verification Complete!*\n\n"
                f"Hi {passport.get('guest_name', 'Guest')}, your passport has been successfully verified. "
                f"Welcome to Easy-Bali! You're all set for your stay."
            )
            await send_whatsapp_message(user_id, msg)
        return {"success": True, "message": "Passport verified and guest notified"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.put("/passports/{passport_id}/reject")
async def reject_passport(passport_id: str, body: Dict[str, Any] = {}) -> Dict[str, Any]:
    from app.utils.whatsapp_func import send_whatsapp_message
    reason = body.get("reason", "The document could not be verified. Please resubmit a clearer copy.")
    try:
        passport = await passport_collection.find_one({"_id": ObjectId(passport_id)})
        if not passport:
            return {"success": False, "error": "Passport submission not found"}
        await passport_collection.update_one(
            {"_id": ObjectId(passport_id)},
            {"$set": {"status": "rejected", "rejection_reason": reason, "rejected_at": datetime.utcnow()}}
        )
        user_id = passport.get("user_id")
        if user_id:
            msg = (
                f"❌ *Verification Update*\n\n"
                f"Hi {passport.get('guest_name', 'Guest')}, unfortunately your passport submission could not be verified.\n\n"
                f"*Reason:* {reason}\n\n"
                f"Please resubmit a clearer copy of your document. Thank you!"
            )
            await send_whatsapp_message(user_id, msg)
        return {"success": True, "message": "Passport rejected and guest notified"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.patch("/issues/{issue_id}/status")
async def update_issue_status_dashboard(
    issue_id: str,
    body: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """Dashboard endpoint to update issue status with history tracking."""
    from app.utils.whatsapp_func import send_whatsapp_message
    status = body.get("status")
    note = body.get("note", f"Status updated to {status}")
    if not status:
        return {"success": False, "error": "status field required"}
    try:
        history_entry = {
            "status": status,
            "timestamp": datetime.utcnow(),
            "note": note
        }
        
        issue = await issue_collection.find_one({"_id": ObjectId(issue_id)})
        if not issue:
            return {"success": False, "error": "Issue not found"}

        result = await issue_collection.update_one(
            {"_id": ObjectId(issue_id)},
            {
                "$set": {"status": status, "updated_at": datetime.utcnow()},
                "$push": {"history": history_entry}
            }
        )
        
        user_id = issue.get("sender_id")
        if user_id:
            formatted_status = status.replace("_", " ").title()
            msg = (
                f"🔧 *Maintenance Update*\n\n"
                f"The status of your reported issue has been updated to: *{formatted_status}*.\n\n"
                f"*Note:* {note}"
            )
            await send_whatsapp_message(user_id, msg)
        
        return {"success": True, "message": f"Issue updated to {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/export/passports")
async def export_passports() -> Response:
    """Export all passport submissions as CSV."""
    records = await passport_collection.find().sort("uploaded_at", -1).to_list(1000)
    rows = []
    for p in records:
        uploaded = p.get("uploaded_at")
        rows.append({
            "ID": str(p.get("_id")),
            "Guest Name": p.get("guest_name", ""),
            "Villa Code": p.get("villa_code", ""),
            "Source": p.get("source", ""),
            "Status": p.get("status", ""),
            "Uploaded At": uploaded.strftime("%Y-%m-%d %H:%M:%S") if hasattr(uploaded, "strftime") else "",
        })

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=passports_export.csv"}
    )


@router.get("/export/issues")
async def export_issues() -> Response:
    """Export all maintenance issues as CSV."""
    records = await issue_collection.find().sort("timestamp", -1).to_list(1000)
    rows = []
    for i in records:
        ts = i.get("timestamp")
        rows.append({
            "ID": str(i.get("_id")),
            "Guest ID": i.get("sender_id", ""),
            "Villa Code": i.get("villa_code", ""),
            "Description": i.get("description", ""),
            "Priority": i.get("priority", ""),
            "Status": i.get("status", ""),
            "Source": i.get("source", ""),
            "Has Media": "Yes" if i.get("media_url") else "No",
            "Timestamp": ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else "",
        })

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=issues_export.csv"}
    )

@router.get("/buckets/customers")
async def get_customer_bucket(start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        match_query = {}
        if start_date and end_date:
            match_query["created_at"] = {"$gte": datetime.fromisoformat(start_date), "$lte": datetime.fromisoformat(end_date)}
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$sender_id",
                "total_bookings": {"$sum": 1},
                "total_spent": {"$sum": {"$toDouble": {"$ifNull": ["$payment.paid_amount", 0]}}},
                "last_booking": {"$max": "$created_at"},
                "services": {"$addToSet": "$service_name"}
            }},
            {"$sort": {"total_spent": -1}},
            {"$limit": 50}
        ]
        results = await order_collection.aggregate(pipeline).to_list(50)
        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/buckets/villas")
async def get_villa_bucket(start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        match_query = {}
        if start_date and end_date:
            match_query["created_at"] = {"$gte": datetime.fromisoformat(start_date), "$lte": datetime.fromisoformat(end_date)}
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$villa_code",
                "total_requests": {"$sum": 1},
                "confirmed_requests": {"$sum": {"$cond": [{"$eq": ["$status", "PAID"]}, 1, 0]}},
                "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$payment.paid_amount", 0]}}}
            }},
            {"$sort": {"total_revenue": -1}}
        ]
        results = await order_collection.aggregate(pipeline).to_list(100)
        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/buckets/payments")
async def get_payment_bucket(start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        match_query = {"status": "PAID"}
        if start_date and end_date:
            match_query["updated_at"] = {"$gte": datetime.fromisoformat(start_date), "$lte": datetime.fromisoformat(end_date)}
        payments = await order_collection.find(match_query).sort("updated_at", -1).limit(100).to_list(100)
        formatted_payments = []
        for p in payments:
            payment_info = p.get("payment", {}) or {}
            dist = payment_info.get("distribution_data", {}) or {}
            raw_time = p.get("updated_at") or p.get("created_at")
            time_str = raw_time.isoformat() if hasattr(raw_time, "isoformat") else str(raw_time or "")
            formatted_payments.append({
                "order_id": p.get("order_number"),
                "service": p.get("service_name"),
                "total_paid": float(payment_info.get("paid_amount") or 0),
                "currency": payment_info.get("currency", "IDR"),
                "splits": {
                    "sp_share": float(dist.get("service_provider", {}).get("amount") or 0),
                    "villa_share": float(dist.get("villa", {}).get("amount") or 0),
                    "eb_share": float(dist.get("easy_bali", {}).get("amount") or 0)
                },
                "time": time_str
            })
        return {"success": True, "data": formatted_payments}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/buckets/services")
async def get_service_bucket(start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        match_query = {}
        if start_date and end_date:
            match_query["created_at"] = {"$gte": datetime.fromisoformat(start_date), "$lte": datetime.fromisoformat(end_date)}
        pipeline = [
            {"$match": match_query},
            {"$group": {
                "_id": "$service_name",
                "popularity": {"$sum": 1},
                "revenue": {"$sum": {"$toDouble": {"$ifNull": ["$payment.paid_amount", 0]}}},
                "avg_price": {"$avg": {"$toDouble": {"$ifNull": ["$payment.paid_amount", 0]}}}
            }},
            {"$sort": {"popularity": -1}}
        ]
        results = await order_collection.aggregate(pipeline).to_list(50)
        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/villa/list")
async def list_accessible_villas(user: Annotated[dict, Depends(requires_role("read_only"))]) -> Dict[str, Any]:
    try:
        if "*" in user.get("villa_codes", ["*"]):
            villas = await db["villas"].find({}, {"_id": 0, "villa_code": 1, "name": 1}).to_list(100)
        else:
            villas = [{"villa_code": code} for code in user.get("villa_codes", [])]
        return {"success": True, "villas": villas}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/villa/profile")
async def get_villa_profile(user: Annotated[dict, Depends(requires_role("read_only"))], code: Optional[str] = Query(None)) -> Dict[str, Any]:
    try:
        # Resolve target villa code
        target_code = code
        if not target_code:
            # Default to first villa in user's restricted list if not provided
            if "*" not in user.get("villa_codes", ["*"]):
                target_code = user["villa_codes"][0]
            else:
                return {"success": False, "error": "Please specify a villa code"}

        # Security check: Does user have access to this code?
        if "*" not in user.get("villa_codes", ["*"]) and target_code not in user["villa_codes"]:
            return {"success": False, "error": "Access denied to this villa"}

        profile = await db["villa_profiles"].find_one({"villa_code": target_code})
        if not profile:
            return {
                "success": True, 
                "profile": {
                    "villa_code": target_code,
                    "manager_phone": "",
                    "wifi_name": "",
                    "wifi_password": "",
                    "house_rules": "",
                    "orientation_link": "",
                    "review_link": "",
                    "maps_link": "",
                    "docs": []
                }
            }
        
        profile["_id"] = str(profile["_id"])
        return {"success": True, "profile": profile}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/villa/profile")
async def update_villa_profile(profile_data: Dict[str, Any], user: dict = Depends(requires_role("staff"))) -> Dict[str, Any]:
    try:
        villa_code = profile_data.get("villa_code")
        if not villa_code:
            return {"success": False, "error": "Villa code is required"}

        # Security check
        if "*" not in user.get("villa_codes", ["*"]) and villa_code not in user["villa_codes"]:
            return {"success": False, "error": "Access denied to this villa"}

        await db["villa_profiles"].update_one(
            {"villa_code": villa_code},
            {"$set": {
                "manager_phone": profile_data.get("manager_phone", ""),
                "wifi_name": profile_data.get("wifi_name", ""),
                "wifi_password": profile_data.get("wifi_password", ""),
                "house_rules": profile_data.get("house_rules", ""),
                "orientation_link": profile_data.get("orientation_link", ""),
                "review_link": profile_data.get("review_link", ""),
                "maps_link": profile_data.get("maps_link", ""),
                "docs": profile_data.get("docs", []),
                "updated_at": datetime.utcnow()
            }},
            upsert=True
        )
        return {"success": True, "message": "Villa profile updated successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/history/{entity_type}/{entity_id}")
async def get_detailed_history(entity_type: str, entity_id: str):
    try:
        query = {}
        if entity_type == "customer": query = {"sender_id": entity_id}
        elif entity_type == "villa": query = {"villa_code": entity_id}
        elif entity_type == "service": query = {"service_name": entity_id}
        elif entity_type == "provider": query = {"service_provider_code": entity_id}
        history = await order_collection.find(query).sort("created_at", -1).to_list(100)
        for item in history:
            item["_id"] = str(item["_id"])
            if "created_at" in item: item["created_at"] = item["created_at"].isoformat()
            if "updated_at" in item: item["updated_at"] = item["updated_at"].isoformat()
        return {"success": True, "history": history}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Expected Arrivals (pre-registration for pre-arrival automation) ────────────

guest_reg_collection = db["guest_registrations"]


@router.get("/arrivals/expected")
async def list_expected_arrivals(user: Annotated[dict, Depends(requires_role("staff"))]) -> Dict[str, Any]:
    try:
        villa_filter = {}
        if "*" not in user.get("villa_codes", ["*"]):
            villa_filter = {"villa_code": {"$in": user["villa_codes"]}}
        docs = await guest_reg_collection.find(villa_filter).sort("checkin_date", 1).to_list(200)
        results = []
        for d in docs:
            d["id"] = str(d.pop("_id"))
            for f in ("checkin_date", "checkout_date", "created_at"):
                if isinstance(d.get(f), datetime):
                    d[f] = d[f].isoformat()
            results.append(d)
        return {"success": True, "arrivals": results}
    except Exception as e:
        return {"success": False, "error": str(e), "arrivals": []}


@router.post("/arrivals/expected")
async def create_expected_arrival(
    body: Dict[str, Any],
    user: Annotated[dict, Depends(requires_role("staff"))]
) -> Dict[str, Any]:
    guest_name  = (body.get("guest_name") or "").strip()
    sender_id   = (body.get("sender_id") or "").strip()
    villa_code  = (body.get("villa_code") or "").strip().upper()
    checkin_str = (body.get("checkin_date") or "").strip()
    checkout_str = (body.get("checkout_date") or "").strip()
    eta         = (body.get("eta") or "").strip()

    if not sender_id:
        return {"success": False, "error": "WhatsApp number (sender_id) is required"}
    if not sender_id.isdigit():
        return {"success": False, "error": "sender_id must be digits only (e.g. 628123456789)"}
    if not villa_code:
        return {"success": False, "error": "villa_code is required"}
    if not checkin_str:
        return {"success": False, "error": "checkin_date is required (YYYY-MM-DD)"}

    # Multi-tenant check
    if "*" not in user.get("villa_codes", ["*"]) and villa_code not in user["villa_codes"]:
        return {"success": False, "error": "Access denied to this villa"}

    try:
        checkin_date  = datetime.fromisoformat(checkin_str)
        checkout_date = datetime.fromisoformat(checkout_str) if checkout_str else None
    except ValueError:
        return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}

    now = datetime.utcnow()
    doc = {
        "guest_name":       guest_name,
        "sender_id":        sender_id,
        "villa_code":       villa_code,
        "checkin_date":     checkin_date,
        "checkout_date":    checkout_date,
        "eta":              eta,
        "status":           "expected",
        "pre_arrival_sent": False,
        "awaiting_eta":     False,
        "created_by":       user.get("email", "admin"),
        "created_at":       now,
    }
    result = await guest_reg_collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    for f in ("checkin_date", "checkout_date", "created_at"):
        if isinstance(doc.get(f), datetime):
            doc[f] = doc[f].isoformat()
    return {"success": True, "arrival": doc}


@router.delete("/arrivals/expected/{arrival_id}")
async def delete_expected_arrival(
    arrival_id: str,
    user: Annotated[dict, Depends(requires_role("staff"))]
) -> Dict[str, Any]:
    try:
        doc = await guest_reg_collection.find_one({"_id": ObjectId(arrival_id)})
        if not doc:
            return {"success": False, "error": "Not found"}
        if "*" not in user.get("villa_codes", ["*"]) and doc.get("villa_code") not in user["villa_codes"]:
            return {"success": False, "error": "Access denied"}
        await guest_reg_collection.delete_one({"_id": ObjectId(arrival_id)})
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Refund Management ─────────────────────────────────────────────────────────

@router.get("/refunds")
async def list_refund_requests(
    user: Annotated[dict, Depends(requires_role("read_only"))]
) -> Dict[str, Any]:
    """List all refund requests."""
    try:
        villa_filter = {}
        if "*" not in user.get("villa_codes", ["*"]):
            villa_filter = {"villa_code": {"$in": user["villa_codes"]}}

        refund_collection = db["refund_requests"]
        docs = await refund_collection.find(villa_filter).sort("created_at", -1).to_list(200)
        results = []
        for d in docs:
            d["id"] = str(d.pop("_id"))
            for f in ("created_at", "reviewed_at"):
                if isinstance(d.get(f), datetime):
                    d[f] = d[f].isoformat()
            results.append(d)
        return {"success": True, "refunds": results}
    except Exception as e:
        return {"success": False, "error": str(e), "refunds": []}


@router.post("/refunds")
async def request_refund(
    body: Dict[str, Any],
    user: Annotated[dict, Depends(requires_role("staff"))]
) -> Dict[str, Any]:
    """Admin/staff submits a refund request for a PAID order. Requires admin approval before processing."""
    order_number = (body.get("order_number") or "").strip()
    reason       = (body.get("reason") or "").strip()

    if not order_number:
        return {"success": False, "error": "order_number is required"}
    if not reason:
        return {"success": False, "error": "reason is required"}

    order = await order_collection.find_one({"order_number": order_number})
    if not order:
        return {"success": False, "error": "Order not found"}
    if order.get("status") != "PAID":
        return {"success": False, "error": "Only PAID orders can be refunded"}

    # Multi-tenant check
    if "*" not in user.get("villa_codes", ["*"]) and order.get("villa_code") not in user["villa_codes"]:
        return {"success": False, "error": "Access denied to this order"}

    refund_collection = db["refund_requests"]
    existing = await refund_collection.find_one({"order_number": order_number, "status": {"$in": ["pending", "approved"]}})
    if existing:
        return {"success": False, "error": "A refund request for this order already exists"}

    paid_amount = order.get("payment", {}).get("paid_amount", 0)
    invoice_id  = order.get("payment", {}).get("xendit_invoice_id", "")

    doc = {
        "order_number":     order_number,
        "xendit_invoice_id": invoice_id,
        "guest_id":         order.get("sender_id", ""),
        "service_name":     order.get("service_name", ""),
        "villa_code":       order.get("villa_code", ""),
        "paid_amount":      paid_amount,
        "reason":           reason,
        "status":           "pending",
        "requested_by":     user.get("email", "staff"),
        "created_at":       datetime.utcnow(),
        "reviewed_at":      None,
        "reviewed_by":      None,
        "xendit_refund_id": None,
    }
    result = await refund_collection.insert_one(doc)
    return {"success": True, "refund_id": str(result.inserted_id), "message": "Refund request submitted. Awaiting admin approval."}


@router.post("/refunds/{refund_id}/approve")
async def approve_refund(
    refund_id: str,
    user: Annotated[dict, Depends(requires_role("admin"))]
) -> Dict[str, Any]:
    """Admin approves refund — calls Xendit refund API and notifies guest via WhatsApp."""
    import httpx, base64, os
    from app.settings.config import settings

    refund_collection = db["refund_requests"]
    try:
        doc = await refund_collection.find_one({"_id": ObjectId(refund_id)})
    except Exception:
        return {"success": False, "error": "Invalid refund ID"}

    if not doc:
        return {"success": False, "error": "Refund request not found"}
    if doc.get("status") != "pending":
        return {"success": False, "error": f"Refund is already {doc.get('status')}"}

    invoice_id  = doc.get("xendit_invoice_id", "")
    paid_amount = doc.get("paid_amount", 0)
    guest_id    = doc.get("guest_id", "")
    order_number = doc.get("order_number", "")
    service_name = doc.get("service_name", "")

    if not invoice_id:
        return {"success": False, "error": "No Xendit invoice ID on record — cannot process refund automatically"}

    # Call Xendit Refund API
    try:
        token = base64.b64encode(f"{settings.XENDIT_SECRET_KEY}:".encode()).decode()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.xendit.co/refunds",
                headers={
                    "Authorization": f"Basic {token}",
                    "Content-Type": "application/json",
                    "idempotency-key": f"refund_{order_number}",
                },
                json={
                    "invoice_id": invoice_id,
                    "reason": doc.get("reason", "requested_by_customer"),
                }
            )
            resp.raise_for_status()
            xendit_result = resp.json()
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        await refund_collection.update_one(
            {"_id": ObjectId(refund_id)},
            {"$set": {"status": "failed", "error": error_detail, "reviewed_at": datetime.utcnow(), "reviewed_by": user.get("email")}}
        )
        return {"success": False, "error": f"Xendit refund failed: {error_detail}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    xendit_refund_id = xendit_result.get("id", "")

    # Mark order as refunded
    await order_collection.update_one(
        {"order_number": order_number},
        {"$set": {"status": "REFUNDED", "payment.refund_id": xendit_refund_id}}
    )

    # Mark refund request as approved
    await refund_collection.update_one(
        {"_id": ObjectId(refund_id)},
        {"$set": {
            "status": "approved",
            "xendit_refund_id": xendit_refund_id,
            "reviewed_at": datetime.utcnow(),
            "reviewed_by": user.get("email"),
        }}
    )

    # Notify guest via WhatsApp
    if guest_id:
        try:
            from app.utils.whatsapp_func import send_whatsapp_message
            await send_whatsapp_message(
                guest_id,
                f"✅ *Refund Processed*\n\n"
                f"Your refund for *{service_name}* (Order {order_number}) of "
                f"IDR {paid_amount:,.0f} has been approved and is being processed.\n\n"
                f"Funds typically arrive within 3–5 business days depending on your bank."
            )
        except Exception as e:
            pass  # Don't fail the refund if WhatsApp notification fails

    return {"success": True, "xendit_refund_id": xendit_refund_id, "message": "Refund approved and processed."}


@router.post("/refunds/{refund_id}/reject")
async def reject_refund(
    refund_id: str,
    body: Dict[str, Any],
    user: Annotated[dict, Depends(requires_role("admin"))]
) -> Dict[str, Any]:
    """Admin rejects a refund request."""
    refund_collection = db["refund_requests"]
    try:
        doc = await refund_collection.find_one({"_id": ObjectId(refund_id)})
    except Exception:
        return {"success": False, "error": "Invalid refund ID"}

    if not doc:
        return {"success": False, "error": "Refund request not found"}
    if doc.get("status") != "pending":
        return {"success": False, "error": f"Refund is already {doc.get('status')}"}

    rejection_note = (body.get("note") or "").strip()
    await refund_collection.update_one(
        {"_id": ObjectId(refund_id)},
        {"$set": {
            "status": "rejected",
            "rejection_note": rejection_note,
            "reviewed_at": datetime.utcnow(),
            "reviewed_by": user.get("email"),
        }}
    )

    # Notify guest
    guest_id = doc.get("guest_id", "")
    if guest_id:
        try:
            from app.utils.whatsapp_func import send_whatsapp_message
            await send_whatsapp_message(
                guest_id,
                f"ℹ️ *Refund Update*\n\n"
                f"Your refund request for *{doc.get('service_name', 'your booking')}* "
                f"(Order {doc.get('order_number', '')}) was reviewed and could not be approved at this time.\n\n"
                f"Please contact our support team if you have questions."
            )
        except Exception:
            pass

    return {"success": True, "message": "Refund request rejected."}
