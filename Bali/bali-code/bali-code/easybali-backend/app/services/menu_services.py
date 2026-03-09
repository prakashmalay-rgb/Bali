import pandas as pd
from app.services.google_sheets import get_workbook
from app.utils.data_processing import clean_dataframe
import threading
from datetime import datetime

import os
import logging

logger = logging.getLogger(__name__)

# Google Sheet configurations
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1tuGBnQFjDntJQglofA17uHhiyekkVyDoSInErbwfR24")

_workbook = None

def get_cached_workbook():
    global _workbook
    if _workbook is None:
        from app.services.google_sheets import get_workbook
        _workbook = get_workbook(SHEET_ID)
    return _workbook

# Cache for storing data
cache = {
    "menu_df": None,
    "services_df": None,
    "design_df": None,
    "last_updated": None,
    "main_menu_design": None,
    "service_providers": None,
    "villas_data": None,
    "price_distribution": None,
    "archive_df": None,
    "platform_design_df": None,
    "price_diff_df": None,
    "price_diff_sp_df": None
}

# Refresh thread control
should_stop = False
refresh_thread = None

def load_data_into_cache():
    """Loads data from Google Sheets into cache with individual sheet resilience."""
    print(f"Refreshing data at {datetime.now()}...")
    try:
        workbook = get_cached_workbook()
        
        # Helper to load a sheet safely
        def safe_load(sheet_name, cache_key, use_clean=True):
            try:
                ws = workbook.worksheet(sheet_name)
                data = ws.get_all_values()
                if not data:
                    logger.warning(f"Sheet '{sheet_name}' is empty.")
                    return
                
                if use_clean:
                    cache[cache_key] = clean_dataframe(data)
                else:
                    df = pd.DataFrame(data[1:], columns=data[0])
                    cache[cache_key] = df
                logger.info(f"✅ Loaded sheet: {sheet_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load sheet '{sheet_name}': {e}")

        # Core worksheets
        safe_load("Menu Structure", "menu_df")
        safe_load("Services Overview", "services_df")
        safe_load("Mark-up", "price_distribution")
        safe_load("Services Providers", "service_providers")
        safe_load("QR Codes", "villas_data")
        safe_load("Services Designs", "design_df")
        safe_load("Menu Design", "main_menu_design")
        
        # Optional / Extended worksheets
        safe_load("Archive", "archive_df")
        safe_load("Platform Design", "platform_design_df")
        safe_load("Price Diff", "price_diff_df")
        safe_load("Price Diff SP", "price_diff_sp_df")
        safe_load("AI Data", "ai_data_df")
        
        cache["last_updated"] = datetime.now()
    except Exception as e:
        logger.error(f"Critical error in load_data_into_cache: {e}")

def schedule_data_refresh():
    """Runs data refresh at regular intervals."""
    global should_stop
    while not should_stop:
        load_data_into_cache()
        for _ in range(300):
            if should_stop:
                break
            threading.Event().wait(1)

def start_cache_refresh():
    """Starts the background thread for refreshing data."""
    global refresh_thread
    refresh_thread = threading.Thread(target=schedule_data_refresh, daemon=True)
    refresh_thread.start()

def stop_cache_refresh():
    """Stops the background thread for refreshing data."""
    global should_stop, refresh_thread
    should_stop = True
    if refresh_thread:
        refresh_thread.join()
        refresh_thread = None

async def get_main_menu():
    if cache["menu_df"] is None:
        raise ValueError("Data not loaded")
    return cache["menu_df"]['Main Menu'].dropna().unique().tolist()


async def get_main_menu_design():
    if cache["main_menu_design"] is None:
        raise ValueError("Data not loaded")
    return cache["main_menu_design"]


async def get_service_providers():
    if cache["service_providers"] is None:
        raise ValueError("Data not loaded")
    return cache["service_providers"]

async def get_villa_data():
    if cache["villas_data"] is None:
        raise ValueError("Data not loaded")
    return cache["villas_data"]


async def get_price_distribution():
    if cache["price_distribution"] is None:
        raise ValueError("Data not loaded")
    return cache["price_distribution"]


async def get_service_overview():
    if cache["services_df"] is None:
        raise ValueError("Data not loaded")
    return cache["services_df"]



async def get_categories():
    if cache["design_df"] is None:
        raise ValueError("Data not loaded")
    categories = cache["design_df"].drop_duplicates(subset=["Category"])[
        ["Category", "Category Description WA"]
    ]

    result = []

    for _, category_row in categories.iterrows():
        category_name = category_row["Category"]
        category_description = category_row["Category Description WA"]

        subcategories = cache["design_df"][
            cache["design_df"]["Category"] == category_name
        ][["Sub-category", "Sub-category Description WA"]].drop_duplicates()

        section_rows = [
            {
                "id": row["Sub-category"].lower().replace(" ", "_"),
                "service_title": row["Sub-category"],
                "service_description": row["Sub-category Description WA"]
            }
            for _, row in subcategories.iterrows()
        ]
        result.append(
            {
                "title": category_name,  # Category name as header
                "description": category_description,  # Category description as body
                "sections": section_rows  # Sections contain subcategories
            }
        )

    return result



async def get_categories_only():
    if cache["design_df"] is None:
        raise ValueError("Data not loaded")
    
    categories = cache["design_df"].drop_duplicates(subset=["Category"])[
        ["Category", "Category ID", "Category Description WA"]
    ]

    result = []

    for _, category_row in categories.iterrows():
        category_id = category_row["Category ID"] 
        category_name = category_row["Category"]
        category_description = category_row["Category Description WA"]

        result.append(
            {
                "id": category_id,
                "title": category_name,
                "description": category_description
            }
        )

    return result

async def get_category_sections(category_title: str):
    if cache["design_df"] is None:
        raise ValueError("Data not loaded")
    if category_title not in cache["design_df"]["Category"].values:
        raise ValueError(f"Category '{category_title}' not found")
    subcategories = cache["design_df"][
        cache["design_df"]["Category"] == category_title
    ][["Sub-category", "Sub-category Description WA"]].drop_duplicates()

    section_rows = []

    for _, row in subcategories.iterrows():
        section_rows.append(
            {
                "id": row["Sub-category"].lower().replace(" ", "_"),
                "title": row["Sub-category"],
                "description": row["Sub-category Description WA"]
            }
        )
    result =  section_rows
    return result


async def get_sub_menu(menu_location: str):
    if cache.get("main_menu_design") is None:
        raise ValueError("Main menu design data not loaded")
    
    df = cache["main_menu_design"]
    filtered_df = df[df["Menu Location"] == menu_location]
    if filtered_df.empty:
        raise ValueError(f"Menu location '{menu_location}' not found")
    
    # Get the main title and description from the row where Title matches Menu Location
    main_row = df[df["Title"] == menu_location]
    if main_row.empty:
        main_title = menu_location
        main_description = ""
    else:
        main_title = main_row.iloc[0]["Title"]
        main_description = main_row.iloc[0].get("Description WA", "")
    
    items = [
        {
            "category": row["Title"],
            "description": row["Description"],
            "picture": row["Picture"],
            "button": row["Button"]
        }
        for _, row in filtered_df.drop_duplicates(subset=["Title"]).iterrows()
    ]
    
    return {
        "main_title": main_title,
        "main_description": main_description,
        "items": items
    }


async def get_restaurants_menu(menu_location: str):
    if cache.get("main_menu_design") is None:
        raise ValueError("Main menu design data not loaded")
    
    df = cache["main_menu_design"]
    filtered_df = df[df["Menu Location"] == menu_location]
    if filtered_df.empty:
        raise ValueError(f"Menu location '{menu_location}' not found")
    return [
        {
            "category": row["Title"],
            "description": row["Description"],
            "picture": row["Picture"],
            "button": row["Button"],
            "Description":row["Description WA"]
        }
        for _, row in filtered_df.drop_duplicates(subset=["Title"]).iterrows()
    ]



async def get_order_service_sub_menu(main_menu: str):
    if main_menu == "Order Services":
        if cache["design_df"] is None:
            raise ValueError("Services data not loaded")

        # Build JSON objects from design_df for "Order Services"
        return [
            {
                "category": row["Category"],
                "description": row["Category Description"],
                "picture": row["Category Picture"],
                "button": row["Category Button"]
            }
            for _, row in cache["design_df"].drop_duplicates(subset=["Category"]).iterrows()
        ]
    if cache["menu_df"] is None:
        raise ValueError("Menu data not loaded")
    
    filtered_df = cache["menu_df"][cache["menu_df"]['Main Menu'] == main_menu]
    if filtered_df.empty:
        raise ValueError("Main menu not found")
    return [
        {
            "category": row["Category"],
            "description": row["Category Description"],
            "picture": row["Category Picture"],
            "button": row["Category Button"]
        }
        for _, row in filtered_df.drop_duplicates(subset=["Category"]).iterrows()
    ]

async def get_sub_sub_menu(main_menu: str, sub_menu: str):
    if cache["menu_df"] is None:
        raise ValueError("Menu data not loaded")
    filtered_df = cache["menu_df"][
        (cache["menu_df"]['Main Menu'] == main_menu) & (cache["menu_df"]['Category'] == sub_menu)
    ]
    if filtered_df.empty:
        raise ValueError("Sub-menu not found")
    return filtered_df['Sub-category'].dropna().tolist()


async def get_sub_category(category: str):
    if cache["design_df"] is None:
        raise ValueError("Services data not loaded")
    filtered_df = cache["design_df"][cache["design_df"]['Category'] == category]
    if filtered_df.empty:
        raise ValueError("Category not found")
    return [
        {
            "subcategory": row["Sub-category"],
            "description": row["Sub-category Description"],
            "picture": row["Sub-category Picture"],
            "button": row["Sub-category Button"]
        }
        for _, row in filtered_df.drop_duplicates(subset=["Sub-category"]).iterrows()
    ]


async def get_service_items(subcategory: str):
    if cache["services_df"]is None:
         raise ValueError("Services data not loaded")
    filtered_df = cache["services_df"][cache["services_df"]['Sub-category'] == subcategory]
    if filtered_df.empty:
        raise ValueError("Category not found")
    return [
        {
            "service_item": row["Service Item"],
            "description": row["Service Item Description"],
            "picture": row["Image URL"],
            "button": row["Final Price (Service Item Button)"],
            "service_provider_code": row.get("Service Provider Number"), # Assuming this column exists based on common patterns
        }
        for _, row in filtered_df.drop_duplicates(subset=["Service Item"]).iterrows()
    ]


async def get_service_base_price(service_name: str) -> str:
    if cache["services_df"] is None:
        raise ValueError("Services data not loaded")
    
    df = cache["services_df"]
    filtered_df = df[df['Service Item'] == service_name]
    
    if filtered_df.empty:
        # Fallback: Normalize all non-alphanumeric characters for maximum matching flexibility
        import re
        norm_input = re.sub(r'[^a-z0-9]', '', str(service_name).lower())
        for idx, row in df.iterrows():
            item = str(row['Service Item'])
            norm_item = re.sub(r'[^a-z0-9]', '', item.lower())
            if norm_input == norm_item or norm_input in norm_item or norm_item in norm_input:
                filtered_df = df.iloc[[idx]]
                break

    if filtered_df.empty:
        print(f"Warning: Service '{service_name}' not found in services data")
        return "0"
        
    price = filtered_df.iloc[0]["Final Price (Service Item Button)"]
    if pd.isna(price):
        return "0"
    # Strip non-breaking spaces, commas, and non-numeric garbage from Google Sheets
    import re as _re
    cleaned = _re.sub(r'[^\d]', '', str(price))
    return cleaned if cleaned else "0"

async def get_service_items_for_whatsapp(subcategory_title: str):
    if cache["services_df"]is None:
         raise ValueError("Services data not loaded")
    filtered_df = cache["services_df"][cache["services_df"]['Sub-category'] == subcategory_title]
    if filtered_df.empty:
        raise ValueError("Category not found")
    return [
        {
            "title": row["Service Item"],
            "description": row["Service Item Description"],
            "button": row["Final Price (Service Item Button)"],
        }
        for _, row in filtered_df.drop_duplicates(subset=["Service Item"]).iterrows()
    ]




async def get_service_provider_by_whatsapp(whatsapp_number: str):
    try:
        providers_df = await get_service_providers()
        clean_whatsapp = whatsapp_number.lstrip('+')
        matching_provider = providers_df[
            (providers_df["WhatsApp"] == whatsapp_number) |
            (providers_df["WhatsApp"] == clean_whatsapp) |
            (providers_df["WhatsApp"] == f"+{clean_whatsapp}")
        ]
        
        if matching_provider.empty:
            return None
        return matching_provider.iloc[0]["Number"]
        
    except Exception as e:
        print(f"Error retrieving service provider: {e}")
        return None
    


async def get_villa_code_by_name(villa_name: str):
    if cache["villas_data"] is None or cache["villas_data"].empty:
        logger.warning("Villa data not loaded into cache.")
        return None
    
    try:
        villas_df = cache["villas_data"]
        search_input = villa_name.strip().lower()
        
        # 1. Search by Number (ID) - Check if input contains the code (robust for 'villa V2')
        for _, row in villas_df.iterrows():
            code = str(row.get("Number", "")).strip().lower()
            if code and (code == search_input or f" {code}" in f" {search_input}"):
                return str(row["Number"]).strip()
        
        # 2. Search by Name - Exact match
        matching_villa = villas_df[
            villas_df["Name of Villa"].astype(str).str.strip().str.lower() == search_input
        ]
        if not matching_villa.empty:
            return str(matching_villa.iloc[0]["Number"]).strip()

        # 3. Search by Name - Check if input contains the name (robust for 'Villa Hassan Umalas')
        for _, row in villas_df.iterrows():
            name = str(row.get("Name of Villa", "")).strip().lower()
            if name and name in search_input:
                return str(row["Number"]).strip()

        # 4. Search by Name - Check if name contains input (Partial match fallback)
        matching_villa = villas_df[
            villas_df["Name of Villa"].astype(str).str.contains(villa_name, case=False, na=False)
        ]
        if not matching_villa.empty:
            return str(matching_villa.iloc[0]["Number"]).strip()
            
        return None
    
    except Exception as e:
        logger.error(f"Error in get_villa_code_by_name: {e}")
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving villa code for '{villa_name}': {e}")
        return None

async def get_villa_location_by_code(villa_code: str):
    if cache["villas_data"] is None:
        return None
    
    try:
        villas_df = cache["villas_data"]
        matching_villa = villas_df[villas_df["Number"] == villa_code]
        
        if matching_villa.empty:
            return None
            
        return matching_villa.iloc[0].get("Location")
        
    except Exception as e:
        print(f"Error retrieving villa location: {e}")
        return None
async def get_villa_info_by_code(villa_code: str):
    """Retrieves full villa metadata by its code."""
    if cache["villas_data"] is None or cache["villas_data"].empty:
        return None
    try:
        df = cache["villas_data"]
        match = df[df["Number"] == villa_code]
        if match.empty:
            return None
        row = match.iloc[0]
        return {
            "name": row.get("Name of Villa"),
            "location": row.get("Location"),
            "address": row.get("Address"),
            "directions": row.get("Directions"),
            "manager_name": row.get("Manager"),
            "manager_number": row.get("Manager Number"),
            "wifi_name": row.get("WiFi Name"),
            "wifi_password": row.get("WiFi Password"),
            "house_rules": row.get("Rules"),
            "map_link": row.get("Map Link")
        }
    except Exception as e:
        logger.error(f"Error in get_villa_info_by_code: {e}")
        return None
