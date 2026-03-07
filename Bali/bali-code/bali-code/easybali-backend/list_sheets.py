import gspread
from google.oauth2.service_account import Credentials
import os
import json
from dotenv import load_dotenv

load_dotenv()

def list_sheets():
    try:
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        CREDENTIALS_FILE = "easy-bali-b74b61110525.json"
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet_id = "1tuGBnQFjDntJQglofA17uHhiyekkVyDoSInErbwfR24"
        wb = client.open_by_key(spreadsheet_id)
        print(f"SHEETS: {[s.title for s in wb.worksheets()]}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    list_sheets()
