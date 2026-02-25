import os
import json
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

# Configurations (Syncing with backend settings)
SHEET_ID = "1tuGBnQFjDntJQglofA17uHhiyekkVyDoSInErbwfR24"
OUTPUT_FILE = "Services Sheet.xlsx"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Load credentials from env var (same as backend)
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

def sync_google_sheets():
    print("🚀 Starting sync from Google Sheets to local XLSX...")
    
    try:
        # 1. Authorize
        if GOOGLE_SERVICE_ACCOUNT_JSON:
            service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
            creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        else:
            # Fallback to file if exists
            creds_file = "easy-bali-b74b61110525.json"
            if os.path.exists(creds_file):
                creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
            else:
                print("❌ No credentials found. Set GOOGLE_SERVICE_ACCOUNT_JSON or provide easy-bali-b74b61110525.json")
                return

        client = gspread.authorize(creds)
        
        # 2. Open Workbook
        workbook = client.open_by_key(SHEET_ID)
        worksheets = workbook.worksheets()
        print(f"📄 Found {len(worksheets)} worksheets.")

        # 3. Download each sheet to a DataFrame and save to Excel
        with pd.ExcelWriter(OUTPUT_FILE, engine='xlsxwriter') as writer:
            for sheet in worksheets:
                print(f"📥 Downloading: {sheet.title}...")
                data = sheet.get_all_values()
                if not data:
                    print(f"⚠️ Sheet {sheet.title} is empty, skipping.")
                    continue
                
                df = pd.DataFrame(data[1:], columns=data[0])
                # Excel has a 31 char limit for sheet names
                sheet_name = sheet.title[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
        print(f"✅ Successfully synced all sheets to {OUTPUT_FILE}")
        print("💡 You can now commit this file to Git Main to keep it synchronized.")

    except Exception as e:
        print(f"💥 Error during sync: {e}")

if __name__ == "__main__":
    sync_google_sheets()
