import json
import gspread
from google.oauth2.service_account import Credentials
from app.settings.config import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = "easy-bali-b74b61110525.json"

def get_workbook(sheet_id: str):
    if settings.GOOGLE_SERVICE_ACCOUNT_JSON:
        service_account_info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)
