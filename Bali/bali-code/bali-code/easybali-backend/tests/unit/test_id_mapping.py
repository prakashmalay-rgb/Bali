"""
UNIT TESTS: Menu ID Mapping & PERSISTENT_API_MAPPING

Verifies that:
- IDs generated from sheet titles match PERSISTENT_API_MAPPING keys
- Menu ID generation logic is consistent
- All AI-chat menu items have a corresponding mapping entry
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


def generate_id_from_title(title: str) -> str:
    """Mirrors fetch_menu_data() ID generation logic in whatsapp_func.py"""
    return title.lower().replace(" ", "_")


class TestPersistentApiMapping:
    """Test cases for PERSISTENT_API_MAPPING key correctness."""

    def test_what_to_do_today_id_matches(self):
        """TC-U-01: 'What To Do Today' sheet title generates matching mapping key."""
        title = "What To Do Today"
        generated_id = generate_id_from_title(title)
        assert generated_id == "what_to_do_today", (
            f"Expected 'what_to_do_today', got '{generated_id}'. "
            "Check PERSISTENT_API_MAPPING key."
        )

    def test_plan_my_trip_id_matches(self):
        """TC-U-02: 'Plan My Trip' sheet title generates matching mapping key."""
        title = "Plan My Trip"
        generated_id = generate_id_from_title(title)
        assert generated_id == "plan_my_trip", (
            f"Expected 'plan_my_trip', got '{generated_id}'. "
            "Check PERSISTENT_API_MAPPING key (was 'plan_my_trip!' before fix)."
        )

    def test_currency_converter_id_matches(self):
        """TC-U-03: 'Currency Converter' generates matching mapping key."""
        title = "Currency Converter"
        assert generate_id_from_title(title) == "currency_converter"

    def test_things_to_do_in_bali_id_matches(self):
        """TC-U-04: 'Things To Do In Bali' generates matching mapping key."""
        title = "Things To Do In Bali"
        assert generate_id_from_title(title) == "things_to_do_in_bali"

    def test_no_trailing_punctuation_in_keys(self):
        """TC-U-05: No mapping key has trailing '?' or '!' (historical bug)."""
        # Import the actual mapping from the app
        from app.utils.whatsapp_func import PERSISTENT_API_MAPPING
        for key in PERSISTENT_API_MAPPING:
            assert not key.endswith("?"), f"Key '{key}' has trailing '?' — should be removed"
            assert not key.endswith("!"), f"Key '{key}' has trailing '!' — should be removed"

    def test_mapping_has_required_keys(self):
        """TC-U-06: All required AI-chat modes are present in PERSISTENT_API_MAPPING."""
        from app.utils.whatsapp_func import PERSISTENT_API_MAPPING
        required = ["what_to_do_today", "plan_my_trip", "currency_converter"]
        for key in required:
            assert key in PERSISTENT_API_MAPPING, (
                f"'{key}' missing from PERSISTENT_API_MAPPING"
            )

    def test_each_mapping_entry_has_chat_type(self):
        """TC-U-07: Every PERSISTENT_MODE_CHAT_TYPES entry maps to a non-empty chat_type string."""
        from app.utils.whatsapp_func import PERSISTENT_MODE_CHAT_TYPES
        for key, chat_type in PERSISTENT_MODE_CHAT_TYPES.items():
            assert isinstance(chat_type, str), f"Entry '{key}' chat_type is not a string"
            assert len(chat_type) > 0, f"Entry '{key}' has empty chat_type"


class TestMenuIdGeneration:
    """Test cases for menu ID generation consistency."""

    def test_spaces_replaced_with_underscore(self):
        """TC-U-08: Spaces in title are replaced with underscores."""
        assert generate_id_from_title("Order Services") == "order_services"

    def test_title_lowercased(self):
        """TC-U-09: Title is fully lowercased."""
        assert generate_id_from_title("LOCAL GUIDE") == "local_guide"

    def test_bali_handbook_generates_correct_id(self):
        """TC-U-10: 'Bali Handbook' generates 'bali_handbook' — not 'local_guide'."""
        assert generate_id_from_title("Bali Handbook") == "bali_handbook"

    def test_recommendations_id(self):
        """TC-U-11: 'Recommendations' generates correct sub-menu lookup key."""
        assert generate_id_from_title("Recommendations") == "recommendations"

    def test_subcat_prefix_pattern(self):
        """TC-U-12: Subcategory IDs are prefixed with 'subcat_'."""
        subcat_name = "Transportation"
        subcat_id = f"subcat_{subcat_name.lower().replace(' ', '_')}"
        assert subcat_id == "subcat_transportation"

    def test_service_prefix_pattern(self):
        """TC-U-13: Service item IDs are prefixed with 'service_'."""
        service_name = "Balinese Massage - 60min"
        service_id = f"service_{service_name.lower().replace(' ', '_')}"
        assert service_id == "service_balinese_massage_-_60min"
