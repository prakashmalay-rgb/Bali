import pandas as pd
from app.services.menu_services import cache, load_data_into_cache
from datetime import datetime

def verify_mapping():
    print(f"Loading data from Google Sheets at {datetime.now()}...")
    try:
        load_data_into_cache()
        df = cache.get("villas_data")
        if df is not None:
            print(f"Villa Data Loaded. Total rows: {len(df)}")
            
            # Search for V1
            v1_row = df[df["Number"].astype(str).str.strip().str.upper() == "V1"]
            if not v1_row.empty:
                print("V1 Mapping Found:")
                print(v1_row.iloc[0].to_dict())
            else:
                print("V1 NOT FOUND")
            
            # Search for S1
            s1_row = df[df["Number"].astype(str).str.strip().str.upper() == "S1"]
            if not s1_row.empty:
                print("S1 Mapping Found:")
                print(s1_row.iloc[0].to_dict())
            else:
                print("S1 NOT FOUND")
        else:
            print("villas_data cache is empty.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    verify_mapping()
