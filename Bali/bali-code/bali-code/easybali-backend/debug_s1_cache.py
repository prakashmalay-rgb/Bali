import asyncio
import pandas as pd
from app.services.menu_services import cache, load_data_into_cache

async def debug_villa_cache():
    print("🚀 Loading data from Google Sheets into cache...")
    try:
        await load_data_into_cache()
        v_df = cache.get("villas_data")
        if v_df is not None:
            print("\n✅ Villa Data Found in Cache!")
            print(f"Columns: {v_df.columns.tolist()}")
            print("\nFirst 5 rows:")
            print(v_df.head(5))
            
            # Specifically check for S1
            print("\n🔍 Searching for 'S1' in 'Number' column...")
            s1_match = v_df[v_df["Number"].astype(str).str.upper() == "S1"]
            if not s1_match.empty:
                print("Found S1 match!")
                print(s1_match)
            else:
                print("S1 NOT FOUND in 'Number' column.")
                
            # Check 'Name of Villa'
            print("\n🔍 Searching for 'S1' in 'Name of Villa' column...")
            s1_name_match = v_df[v_df["Name of Villa"].astype(str).str.upper() == "S1"]
            if not s1_name_match.empty:
                print("Found S1 match by name!")
                print(s1_name_match)
            else:
                print("S1 NOT FOUND in 'Name of Villa' column.")
        else:
            print("❌ No villa data in cache.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_villa_cache())
