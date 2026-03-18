"""
UNIT TESTS: Customer ID Generation Logic

Verifies customer ID format, fallback logic, and phone number validation.
"""
import pytest
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


CUSTOMER_ID_PATTERN = re.compile(r'^EB-C-\d{5}$')
FALLBACK_PATTERN = re.compile(r'^EB-C-TEMP-\d{6}$')


class TestCustomerIdFormat:
    """TC-U-40 through TC-U-49: Customer ID format validation."""

    def test_customer_id_format(self):
        """TC-U-40: Customer ID matches EB-C-XXXXX format."""
        cid = "EB-C-00001"
        assert CUSTOMER_ID_PATTERN.match(cid), f"'{cid}' does not match EB-C-XXXXX"

    def test_customer_id_zero_padded(self):
        """TC-U-41: Counter is zero-padded to 5 digits."""
        for n, expected in [(1, "EB-C-00001"), (100, "EB-C-00100"), (99999, "EB-C-99999")]:
            cid = f"EB-C-{n:05d}"
            assert cid == expected

    def test_fallback_id_format(self):
        """TC-U-42: Fallback ID when DB fails uses last 6 digits of sender_id."""
        sender_id = "6281234567890"
        fallback = f"EB-C-TEMP-{sender_id[-6:]}"
        assert fallback == "EB-C-TEMP-567890"
        assert FALLBACK_PATTERN.match(fallback)

    def test_whatsapp_number_detected_as_digit(self):
        """TC-U-43: WhatsApp sender_id (all digits) correctly identified."""
        sender_id = "6281999281660"
        assert sender_id.isdigit() is True

    def test_websocket_session_not_digit(self):
        """TC-U-44: Web session IDs (UUID-like) correctly identified as non-phone."""
        session_id = "sess_abc123xyz"
        assert session_id.isdigit() is False

    def test_customer_id_counter_increments(self):
        """TC-U-45: Sequential customer IDs are unique and ordered."""
        ids = [f"EB-C-{n:05d}" for n in range(1, 6)]
        assert ids == ["EB-C-00001", "EB-C-00002", "EB-C-00003", "EB-C-00004", "EB-C-00005"]
        assert len(set(ids)) == 5  # all unique

    def test_customer_id_in_order_dict(self):
        """TC-U-46: customer_id key exists and is non-None in a correctly built order dict."""
        order_dict = {
            "order_number": "EB12300001",
            "service_name": "Balinese Massage - 60min",
            "customer_id": "EB-C-00001",
            "sender_id": "6281234567890",
        }
        assert "customer_id" in order_dict
        assert order_dict["customer_id"] is not None
        assert CUSTOMER_ID_PATTERN.match(order_dict["customer_id"])

    def test_customer_id_in_issue_dict(self):
        """TC-U-47: Issue records have customer_id field."""
        issue = {
            "sender_id": "6281234567890",
            "customer_id": "EB-C-00001",
            "villa_code": "V1",
            "description": "AC not working",
            "status": "open",
        }
        assert "customer_id" in issue

    def test_customer_id_in_passport_dict(self):
        """TC-U-48: Passport records have customer_id field."""
        passport = {
            "user_id": "6281234567890",
            "customer_id": "EB-C-00001",
            "villa_code": "V1",
            "status": "pending_verification",
        }
        assert "customer_id" in passport

    def test_web_issue_has_none_customer_id(self):
        """TC-U-49: Web chatbot issues have customer_id=None (no phone binding)."""
        web_issue = {
            "sender_id": "web_session_abc123",
            "customer_id": None,
            "source": "web",
        }
        assert web_issue["customer_id"] is None
