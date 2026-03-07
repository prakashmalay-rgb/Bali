import asyncio
import gspread
from google.oauth2.service_account import Credentials
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def update_clarence_number():
    try:
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        CREDENTIALS_FILE = "easy-bali-b74b61110525.json"
        
        print("Authenticating to Google Sheets...")
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        spreadsheet_id = "1tuGBnQFjDntJQglofA17uHhiyekkVyDoSInErbwfR24"
        wb = client.open_by_key(spreadsheet_id)
        ws = wb.worksheet("Services Providers")
        
        # Get all records to find Clarence
        records = ws.get_all_records()
        for i, row in enumerate(records):
            # 'Name' column might be 'Name of provider' or 'Name' based on previous checks
            name = str(row.get('Name', ''))
            if 'Clarence' in name:
                # Row index in gspread is 1-based, and we have a header row
                row_idx = i + 2 
                # Let's find the column index for WhatsApp
                header = ws.row_values(1)
                col_idx = header.index("WhatsApp") + 1
                
                print(f"Found Clarence at row {row_idx}, column {col_idx}.")
                print(f"Old Value: {row.get('WhatsApp')}")
                
                # Update cell
                ws.update_cell(row_idx, col_idx, "+6281999281660")
                print("✅ Successfully updated Clarence's number to +6281999281660 in Google Sheets!")
                return
                
        print("Clarence not found in the sheet.")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    update_clarence_number()
