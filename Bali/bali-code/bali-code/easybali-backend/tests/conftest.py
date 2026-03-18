"""
EasyBali Test Configuration
Shared fixtures for all test layers.
"""
import pytest
import os
import sys

# Ensure app is importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

LIVE_API_BASE = "https://bali-v92r.onrender.com"

# Sheet column contracts — the authoritative list of columns the code requires.
# If a sheet is missing any of these, tests will fail and alert us.
REQUIRED_COLUMNS = {
    "Services Overview": [
        "Service Item",
        "Service Item Description",
        "Sub-category",
        "Final Price (Service Item Button)",
        "Service Providers",
        "Image URL",
        "Locations",
    ],
    "Services Designs": [
        "Category",
        "Category ID",
        "Category Description WA",
        "Sub-category",
        "Sub-category Description WA",
    ],
    "Menu Design": [
        "Menu Location",
        "Title",
        "Description",
        "Button",
    ],
    "Services Providers": [
        "Number",
        "Name",
        "WhatsApp",
        "Bank",
        "Account Number",
    ],
    "QR Codes": [
        "Number",
        "Name of Villa",
        "Location",
        "Address",
        "Bank",
        "Account Number",
    ],
    "Mark-up": [
        "Service Item",
        "Vendor Price",
        "Villa Comm",
    ],
    "Menu Structure": [
        "Main Menu",
    ],
    "AI Data": [
        "Service Item",
        "Service Item Description",
        "Price (Service Item Button)",
    ],
}

# Menu items that MUST appear in Main Menu (Menu Design sheet, Menu Location = "Main Menu")
REQUIRED_MAIN_MENU_ITEMS = [
    "Order Services",
    "What To Do Today",
    "Plan My Trip",
    "Currency Converter",
]

# IDs that must resolve to AI chat modes
PERSISTENT_MODE_IDS = [
    "what_to_do_today",
    "plan_my_trip",
    "currency_converter",
    "things_to_do_in_bali",
]
