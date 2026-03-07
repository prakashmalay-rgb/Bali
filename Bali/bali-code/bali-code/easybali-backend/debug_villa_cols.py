import asyncio
import os
import pandas as pd
from app.services.google_sheets import get_workbook
from dotenv import load_dotenv

load_dotenv()

async def debug_villa_cols():
    SHEET_ID = "1tuGBnQFjDntJQglofA17uHhiyekkVyDoSInErbwfR24"
    workbook = get_workbook(SHEET_ID)
    ws = workbook.worksheet("QR Codes")
    data = ws.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    print(f"VILLA COLS: {df.columns.tolist()}")
    print(f"VILLA V1 DATA: {df[df.iloc[:,0] == 'V1'].to_dict('records')}")

if __name__ == '__main__':
    asyncio.run(debug_villa_cols())
