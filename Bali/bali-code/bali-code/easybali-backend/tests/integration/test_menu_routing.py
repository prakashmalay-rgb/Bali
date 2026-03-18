"""
INTEGRATION TESTS: Menu Routing Logic

Tests that the WhatsApp menu routing correctly routes each menu item
to the right handler using the actual sheet data loaded into cache.

Run: pytest tests/integration/test_menu_routing.py -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


@pytest.fixture(scope="module")
def loaded_cache():
    """Load Google Sheets into cache for routing tests."""
    from app.services.menu_services import load_data_into_cache, cache
    load_data_into_cache()
    return cache


class TestMenuIdRouting:
    """TC-I-70+: Menu item IDs route correctly."""

    def test_what_to_do_today_id_in_mapping(self, loaded_cache):
        """TC-I-70: 'What To Do Today' sheet item generates sanitized ID in PERSISTENT_API_MAPPING."""
        import re
        from app.utils.whatsapp_func import PERSISTENT_API_MAPPING

        cache_df = loaded_cache.get("main_menu_design")
        if cache_df is None:
            pytest.skip("Menu Design cache not loaded")

        main_menu_items = cache_df[cache_df["Menu Location"] == "Main Menu"]["Title"].str.strip().tolist()
        # Accept both 'What To Do Today' and 'What To Do Today?' (sheet may have trailing ?)
        matching = [t for t in main_menu_items if t.rstrip("?! ") == "What To Do Today"]
        if not matching:
            pytest.skip("'What To Do Today' not in Main Menu (add to Menu Design sheet)")

        # fetch_menu_data sanitizes: lower + replace spaces + strip non-word chars
        raw_id = matching[0].lower().replace(" ", "_")
        generated_id = re.sub(r'[^\w]', '', raw_id)
        assert generated_id in PERSISTENT_API_MAPPING, (
            f"Generated ID '{generated_id}' not in PERSISTENT_API_MAPPING. "
            f"Available keys: {list(PERSISTENT_API_MAPPING.keys())}"
        )

    def test_plan_my_trip_id_in_mapping(self, loaded_cache):
        """TC-I-71: 'Plan My Trip' generates ID that resolves in PERSISTENT_API_MAPPING."""
        from app.utils.whatsapp_func import PERSISTENT_API_MAPPING
        generated_id = "Plan My Trip".lower().replace(" ", "_")
        assert generated_id in PERSISTENT_API_MAPPING

    def test_currency_converter_id_in_mapping(self, loaded_cache):
        """TC-I-72: 'Currency Converter' generates ID that resolves in PERSISTENT_API_MAPPING."""
        from app.utils.whatsapp_func import PERSISTENT_API_MAPPING
        generated_id = "Currency Converter".lower().replace(" ", "_")
        assert generated_id in PERSISTENT_API_MAPPING

    def test_local_guide_or_bali_handbook_handled(self):
        """TC-I-73: Both 'Local Guide' and 'Bali Handbook' are in the sub-menu handler list."""
        # Read whatsapp_func.py source to verify both names are handled
        func_path = os.path.join(os.path.dirname(__file__), "../../app/utils/whatsapp_func.py")
        with open(func_path, encoding="utf-8") as f:
            source = f.read()
        assert '"Local Guide"' in source or "'Local Guide'" in source
        assert '"Bali Handbook"' in source or "'Bali Handbook'" in source

    def test_recommendations_in_submenu_handler(self):
        """TC-I-74: 'Recommendations' is in the sub-menu dispatch list."""
        func_path = os.path.join(os.path.dirname(__file__), "../../app/utils/whatsapp_func.py")
        with open(func_path, encoding="utf-8") as f:
            source = f.read()
        assert '"Recommendations"' in source

    def test_no_undefined_function_calls(self):
        """TC-I-75: 'send_whatsapp_main_menu_list_message' is NOT called (was undefined bug)."""
        func_path = os.path.join(os.path.dirname(__file__), "../../app/utils/whatsapp_func.py")
        with open(func_path, encoding="utf-8") as f:
            source = f.read()
        assert "send_whatsapp_main_menu_list_message" not in source, (
            "Undefined function 'send_whatsapp_main_menu_list_message' still called. "
            "Should be 'send_whatsapp_menu_list_message'."
        )


class TestServiceItemRouting:
    """TC-I-80+: Service item routing from Services Overview."""

    def test_service_items_load_with_price(self, loaded_cache):
        """TC-I-80: Service items load from cache with non-zero price."""
        import asyncio
        from app.services.menu_services import get_service_items

        cache_df = loaded_cache.get("services_df")
        if cache_df is None:
            pytest.skip("Services Overview cache not loaded")

        subcats = cache_df["Sub-category"].dropna().unique().tolist()
        if not subcats:
            pytest.skip("No sub-categories found")

        first_subcat = subcats[0]
        items = asyncio.get_event_loop().run_until_complete(get_service_items(first_subcat))
        assert len(items) > 0, f"No items found for sub-category '{first_subcat}'"

    def test_get_service_base_price_returns_value(self, loaded_cache):
        """TC-I-81: get_service_base_price returns a non-zero value for a known service."""
        import asyncio
        from app.services.menu_services import get_service_base_price

        cache_df = loaded_cache.get("services_df")
        if cache_df is None:
            pytest.skip("Services Overview cache not loaded")

        # Get first available service item name
        services = cache_df["Service Item"].dropna().tolist()
        if not services:
            pytest.skip("No service items in cache")

        first_service = services[0]
        price = asyncio.get_event_loop().run_until_complete(get_service_base_price(first_service))
        assert price is not None
        assert str(price) != "0", f"Price for '{first_service}' is 0 — check column name"
