"""
INTEGRATION TESTS: Google Sheets Column Contracts

Connects to the live Google Sheets and verifies that every column the code
requires actually exists. Fails loudly if a column is renamed or missing.

Run: pytest tests/integration/test_sheets_columns.py -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from tests.conftest import REQUIRED_COLUMNS


@pytest.fixture(scope="module")
def workbook():
    """Load the Google Sheets workbook once for all tests in this module."""
    from app.services.menu_services import get_cached_workbook
    return get_cached_workbook()


@pytest.fixture(scope="module")
def sheet_frames(workbook):
    """Load all required sheets as DataFrames."""
    import pandas as pd
    from app.utils.data_processing import clean_dataframe
    frames = {}
    for sheet_name in REQUIRED_COLUMNS:
        try:
            ws = workbook.worksheet(sheet_name)
            data = ws.get_all_values()
            frames[sheet_name] = clean_dataframe(data) if data else pd.DataFrame()
        except Exception as e:
            frames[sheet_name] = None
            pytest.fail(f"Could not load sheet '{sheet_name}': {e}")
    return frames


class TestSheetExists:
    """TC-I-01 through TC-I-12: Each required sheet can be opened."""

    @pytest.mark.parametrize("sheet_name", list(REQUIRED_COLUMNS.keys()))
    def test_sheet_loadable(self, sheet_frames, sheet_name):
        """TC-I-01+: Sheet '{sheet_name}' is accessible and not empty."""
        df = sheet_frames.get(sheet_name)
        assert df is not None, f"Sheet '{sheet_name}' could not be loaded"
        assert not df.empty, f"Sheet '{sheet_name}' is empty — check Google Sheets"


class TestRequiredColumns:
    """TC-I-20+: Each required column exists in its sheet."""

    @pytest.mark.parametrize("sheet_name,columns", [
        (sheet, cols)
        for sheet, cols in REQUIRED_COLUMNS.items()
        for cols in [cols]
    ])
    def test_all_required_columns_present(self, sheet_frames, sheet_name, columns):
        """TC-I-20+: All required columns exist in sheet."""
        df = sheet_frames.get(sheet_name)
        if df is None:
            pytest.skip(f"Sheet '{sheet_name}' could not be loaded")
        missing = [col for col in columns if col not in df.columns]
        assert not missing, (
            f"Sheet '{sheet_name}' is missing columns: {missing}\n"
            f"Available columns: {df.columns.tolist()}"
        )


class TestServicesOverview:
    """TC-I-30+: Services Overview specific data quality checks."""

    def test_service_items_not_empty(self, sheet_frames):
        """TC-I-30: Services Overview has at least one service item."""
        df = sheet_frames.get("Services Overview")
        services = df["Service Item"].dropna().tolist()
        assert len(services) > 0, "No service items found in Services Overview"

    def test_prices_are_present(self, sheet_frames):
        """TC-I-31: Final Price column has values for at least 80% of rows."""
        df = sheet_frames.get("Services Overview")
        total = len(df)
        filled = df["Final Price (Service Item Button)"].replace("", None).dropna().shape[0]
        pct = (filled / total) * 100 if total > 0 else 0
        assert pct >= 80, f"Only {pct:.0f}% of service rows have prices (expected ≥80%)"

    def test_service_providers_column_has_values(self, sheet_frames):
        """TC-I-32: At least one service row has Service Providers assigned."""
        df = sheet_frames.get("Services Overview")
        has_providers = df["Service Providers"].replace("", None).dropna()
        assert len(has_providers) > 0, "No service items have Service Providers assigned"

    def test_price_column_name_consistency(self, sheet_frames):
        """TC-I-33: 'Final Price (Service Item Button)' is the correct column name
        (not 'Price (Service Item Button)' which is only in AI Data sheet)."""
        df = sheet_frames.get("Services Overview")
        assert "Final Price (Service Item Button)" in df.columns
        # AI Data sheet uses different column name — verify separation
        ai_df = sheet_frames.get("AI Data")
        if ai_df is not None and not ai_df.empty:
            assert "Price (Service Item Button)" in ai_df.columns, (
                "AI Data sheet missing 'Price (Service Item Button)' — "
                "update ai_prompt.py column reference"
            )


class TestMenuDesign:
    """TC-I-40+: Menu Design sheet structure checks."""

    def test_main_menu_items_exist(self, sheet_frames):
        """TC-I-40: Main Menu items are present in Menu Design sheet."""
        df = sheet_frames.get("Menu Design")
        main_menu_items = df[df["Menu Location"] == "Main Menu"]["Title"].tolist()
        assert len(main_menu_items) > 0, (
            "No items with Menu Location='Main Menu' found in Menu Design sheet"
        )

    def test_what_to_do_today_in_main_menu(self, sheet_frames):
        """TC-I-41: 'What To Do Today' is active in Main Menu."""
        df = sheet_frames.get("Menu Design")
        main_menu = df[df["Menu Location"] == "Main Menu"]["Title"].str.strip().tolist()
        assert "What To Do Today" in main_menu, (
            "'What To Do Today' not found in Main Menu. "
            "Add it with Menu Location='Main Menu' in the Menu Design sheet."
        )

    def test_plan_my_trip_in_main_menu(self, sheet_frames):
        """TC-I-42: 'Plan My Trip' is active in Main Menu."""
        df = sheet_frames.get("Menu Design")
        main_menu = df[df["Menu Location"] == "Main Menu"]["Title"].str.strip().tolist()
        assert "Plan My Trip" in main_menu, (
            "'Plan My Trip' not found in Main Menu. "
            "Add it with Menu Location='Main Menu' in the Menu Design sheet."
        )

    def test_currency_converter_in_main_menu(self, sheet_frames):
        """TC-I-43: 'Currency Converter' is active in Main Menu."""
        df = sheet_frames.get("Menu Design")
        main_menu = df[df["Menu Location"] == "Main Menu"]["Title"].str.strip().tolist()
        assert "Currency Converter" in main_menu, (
            "'Currency Converter' not found in Main Menu."
        )

    def test_recommendations_submenu_has_google_maps(self, sheet_frames):
        """TC-I-44: Recommendations sub-items have Button field with URLs."""
        df = sheet_frames.get("Menu Design")
        recs = df[df["Menu Location"] == "Recommendations"]
        if recs.empty:
            pytest.skip("No 'Recommendations' items in Menu Design sheet yet")
        items_with_buttons = recs[recs["Button"].str.startswith("http", na=False)]
        assert len(items_with_buttons) > 0, (
            "Recommendations sub-items have no Button URLs. "
            "Add Google Maps links in the 'Button' column."
        )


class TestServiceProviders:
    """TC-I-50+: Services Providers sheet checks."""

    def test_providers_have_whatsapp_numbers(self, sheet_frames):
        """TC-I-50: At least one SP has a WhatsApp number."""
        df = sheet_frames.get("Services Providers")
        has_wa = df["WhatsApp"].replace("", None).dropna()
        assert len(has_wa) > 0, "No service providers have WhatsApp numbers"

    def test_whatsapp_numbers_are_numeric_like(self, sheet_frames):
        """TC-I-51: WhatsApp numbers contain digits (handle +62/0 prefix variants)."""
        df = sheet_frames.get("Services Providers")
        wa_numbers = df["WhatsApp"].replace("", None).dropna().tolist()
        import re
        for num in wa_numbers:
            digits = re.sub(r'[^\d]', '', str(num))
            assert len(digits) >= 8, f"WhatsApp number '{num}' has fewer than 8 digits"

    def test_bank_details_present_for_some_providers(self, sheet_frames):
        """TC-I-52: At least one SP has bank details for disbursement."""
        df = sheet_frames.get("Services Providers")
        has_bank = df[df["Bank"].replace("", None).notna() & df["Account Number"].replace("", None).notna()]
        assert len(has_bank) > 0, "No service providers have bank account details for disbursement"


class TestVillaData:
    """TC-I-60+: QR Codes (Villa Data) sheet checks."""

    def test_at_least_one_villa_exists(self, sheet_frames):
        """TC-I-60: At least one villa entry in QR Codes sheet."""
        df = sheet_frames.get("QR Codes")
        assert len(df) > 0

    def test_villa_numbers_are_v_prefixed(self, sheet_frames):
        """TC-I-61: Villa codes follow V1, V2, V3 pattern."""
        df = sheet_frames.get("QR Codes")
        numbers = df["Number"].replace("", None).dropna().tolist()
        v_prefixed = [n for n in numbers if str(n).startswith("V")]
        assert len(v_prefixed) > 0, f"No V-prefixed villa codes found. Got: {numbers[:5]}"
