from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from app.utils.qrutils import generate_and_upload_qrcode
from app.db.session import db
from datetime import datetime
from uuid import uuid4
from typing import Optional, List

router = APIRouter(prefix="/onboarding", tags=["Villa Onboarding"])

villa_collection = db["villas"]

@router.post("/generate-qr")
async def generate_villa_qr(
    villa_name: str = Form(...),
    location: str = Form(...),
    manager_contact: str = Form(...),
    villa_code: Optional[str] = Form(None)
):
    """
    Generates a unique QR code for a villa and stores the mapping in MongoDB.
    """
    try:
        if not villa_code:
            villa_code = f"V{await villa_collection.count_documents({}) + 1}"
        
        # Check if villa_code already exists
        existing = await villa_collection.find_one({"villa_code": villa_code})
        if existing:
            # Append random suffix if collision (unlikely with V count)
            villa_code = f"{villa_code}_{str(uuid4())[:4]}"

        # QR Data: The link that users will scan
        # Format: WEB_BASE_URL/welcome?villa=V1
        from app.settings.config import settings
        welcome_url = f"{settings.WEB_BASE_URL}/welcome?villa={villa_code}"
        
        qr_url = await generate_and_upload_qrcode(welcome_url)
        
        villa_data = {
            "villa_name": villa_name,
            "villa_code": villa_code,
            "location": location,
            "manager_contact": manager_contact,
            "qr_code_url": qr_url,
            "welcome_url": welcome_url,
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        
        await villa_collection.insert_one(villa_data)
        
        return {
            "status": "success",
            "villa_code": villa_code,
            "qr_code_url": qr_url,
            "welcome_url": welcome_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate QR: {str(e)}")

@router.get("/villas")
async def list_villas():
    """List all onboarded villas for the admin panel."""
    villas = []
    async for villa in villa_collection.find({}, {"_id": 0}):
        villas.append(villa)
    return {"villas": villas}

@router.post("/confirm-onboarding")
async def confirm_onboarding(villa_code: str = Form(...), email: str = Form(...)):
    """
    Sends a confirmation email to the villa owner/manager with their QR code.
    (MOCKED implementation - logging only)
    """
    villa = await villa_collection.find_one({"villa_code": villa_code})
    if not villa:
        raise HTTPException(status_code=404, detail="Villa not found")
    
    # Mock email sending
    print(f"📧 Sending confirmation email to {email} for villa {villa['villa_name']}")
    print(f"🔗 QR Code URL: {villa['qr_code_url']}")
    
    return {"status": "success", "message": f"Confirmation email (simulated) sent to {email}"}

from fastapi.responses import HTMLResponse

@router.get("/dashboard", response_class=HTMLResponse)
async def onboarding_dashboard():
    """Simple HTML dashboard to view onboarded villas."""
    villas = await list_villas()
    villa_rows = ""
    for v in villas["villas"]:
        villa_rows += f"""
        <tr>
            <td>{v.get('villa_name')}</td>
            <td><code>{v.get('villa_code')}</code></td>
            <td>{v.get('location')}</td>
            <td><a href="{v.get('qr_code_url')}" target="_blank">View QR</a></td>
            <td><span class="status-{v.get('status')}">{v.get('status')}</span></td>
        </tr>
        """
    
    html_content = f"""
    <html>
        <head>
            <title>Villa Onboarding Dashboard</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f4f7f6; }}
                h1 {{ color: #2c3e50; }}
                table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
                th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #eee; }}
                th {{ background-color: #3498db; color: white; }}
                .status-active {{ color: #27ae60; font-weight: bold; }}
                tr:hover {{ background-color: #f9f9f9; }}
                code {{ background: #eee; padding: 2px 5px; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1>🏝️ Villa Onboarding Admin</h1>
            <table>
                <thead>
                    <tr>
                        <th>Villa Name</th>
                        <th>Code</th>
                        <th>Location</th>
                        <th>QR Code</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {villa_rows}
                </tbody>
            </table>
        </body>
    </html>
    """
    return html_content
