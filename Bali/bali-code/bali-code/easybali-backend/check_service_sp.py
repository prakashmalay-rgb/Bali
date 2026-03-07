import gspread
from google.oauth2.service_account import Credentials
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def check_service_sp():
    try:
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        CREDENTIALS_FILE = "easy-bali-b74b61110525.json"
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet_id = "1tuGBnQFjDntJQglofA17uHhiyekkVyDoSInErbwfR24"
        wb = client.open_by_key(spreadsheet_id)
        ws = wb.worksheet("Services Overview")
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        service = df[df["Service Item"].str.contains("Balinese Massage - 60min", case=False, na=False)]
        print(f"SERVICE INFO: {service[['Service Item', 'Service Providers']].to_dict('records')}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    check_service_sp()
