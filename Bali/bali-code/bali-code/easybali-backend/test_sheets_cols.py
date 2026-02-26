import asyncio
from app.services.menu_services import get_cached_workbook, clean_dataframe
import pandas as pd

def main():
    workbook = get_cached_workbook()
    
    # Check Price distribution
    price_distribution = workbook.worksheet("Mark-up")
    data3 = price_distribution.get_all_values()
    df_price = pd.DataFrame(data3[1:], columns=data3[0]) if data3 else pd.DataFrame()
    print("Mark-up columns:")
    print(df_price.columns.tolist())
    
    # Check Villa Data
    villas = workbook.worksheet("QR Codes")
    data2 = villas.get_all_values()
    df_villa = pd.DataFrame(data2[1:], columns=data2[0]) if data2 else pd.DataFrame()
    print("QR Codes columns:")
    print(df_villa.columns.tolist())

if __name__ == "__main__":
    main()
