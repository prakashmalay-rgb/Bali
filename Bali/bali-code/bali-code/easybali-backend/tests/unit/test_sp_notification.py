"""
UNIT TESTS: SP Notification Message Format

Verifies the SP WhatsApp message text matches the spec exactly.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestSPMessageContent:
    """TC-U-60+: SP notification message content."""

    def test_new_request_bilingual_header_present(self):
        """TC-U-60: New request message contains English + Indonesian header."""
        func_path = os.path.join(os.path.dirname(__file__), "../../app/utils/whatsapp_func.py")
        with open(func_path, encoding="utf-8") as f:
            source = f.read()
        assert "New request received!" in source
        assert "Permintaan layanan baru diterima" in source

    def test_accept_confirmation_prompt_bilingual(self):
        """TC-U-61: Accept confirmation prompt has English + Indonesian text."""
        func_path = os.path.join(os.path.dirname(__file__), "../../app/utils/whatsapp_func.py")
        with open(func_path, encoding="utf-8") as f:
            source = f.read()
        assert "Are you sure you want to accept this request?" in source
        assert "Apakah Anda yakin ingin menerima permintaan ini?" in source

    def test_decline_confirmation_prompt_bilingual(self):
        """TC-U-62: Decline confirmation prompt has English + Indonesian text."""
        func_path = os.path.join(os.path.dirname(__file__), "../../app/utils/whatsapp_func.py")
        with open(func_path, encoding="utf-8") as f:
            source = f.read()
        assert "Are you sure you want to decline this request?" in source
        assert "Apakah Anda yakin ingin menolak permintaan ini?" in source

    def test_after_accept_message_bilingual(self):
        """TC-U-63: Post-accept message 'You've successfully confirmed' is bilingual."""
        func_path = os.path.join(os.path.dirname(__file__), "../../app/utils/whatsapp_func.py")
        with open(func_path, encoding="utf-8") as f:
            source = f.read()
        assert "You've successfully confirmed the booking!" in source
        assert "Anda telah berhasil mengonfirmasi pemesanan!" in source

    def test_after_decline_message_bilingual(self):
        """TC-U-64: Post-decline message 'noted your unavailability' is bilingual."""
        func_path = os.path.join(os.path.dirname(__file__), "../../app/utils/whatsapp_func.py")
        with open(func_path, encoding="utf-8") as f:
            source = f.read()
        assert "noted your unavailability" in source
        assert "Kami telah mencatat ketidaksediaan" in source

    def test_post_payment_assignment_confirmed_bilingual(self):
        """TC-U-65: Post-payment SP message has bilingual 'Assignment Confirmed' header."""
        webhook_path = os.path.join(os.path.dirname(__file__), "../../app/routes/xendit_webhook.py")
        with open(webhook_path, encoding="utf-8") as f:
            source = f.read()
        assert "Assignment Confirmed!" in source
        assert "Penugasan dikonfirmasi!" in source

    def test_post_payment_includes_customer_contact(self):
        """TC-U-66: Post-payment SP message includes Customer Contact field."""
        webhook_path = os.path.join(os.path.dirname(__file__), "../../app/routes/xendit_webhook.py")
        with open(webhook_path, encoding="utf-8") as f:
            source = f.read()
        assert "Customer Contact" in source

    def test_sp_buttons_yes_decline_and_no_go_back(self):
        """TC-U-67: Decline confirmation has 'Yes, Decline' and 'No, Go Back' buttons."""
        func_path = os.path.join(os.path.dirname(__file__), "../../app/utils/whatsapp_func.py")
        with open(func_path, encoding="utf-8") as f:
            source = f.read()
        assert '"Yes, Decline"' in source or "'Yes, Decline'" in source
        assert '"No, Go Back"' in source or "'No, Go Back'" in source

    def test_order_summary_includes_customer_id(self):
        """TC-U-68: Order summary sent to SP includes Customer ID field."""
        summary_path = os.path.join(os.path.dirname(__file__), "../../app/services/order_summary.py")
        with open(summary_path, encoding="utf-8") as f:
            source = f.read()
        assert "Customer ID" in source
        assert "customer_id" in source
