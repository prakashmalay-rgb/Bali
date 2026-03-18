"""
SMOKE TESTS: Live Render API

Hits the production server and verifies critical endpoints respond correctly.
Requires no auth for public endpoints; uses Bearer token for dashboard endpoints.

Run: pytest tests/smoke/test_live_api.py -v
Set env var: EASYBALI_JWT_TOKEN=<your_token> for dashboard tests
"""
import pytest
import httpx
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

BASE = "https://bali-v92r.onrender.com"
JWT_TOKEN = os.getenv("EASYBALI_JWT_TOKEN", "")
AUTH_HEADERS = {"Authorization": f"Bearer {JWT_TOKEN}"} if JWT_TOKEN else {}

TIMEOUT = 20  # seconds — Render may cold-start


@pytest.fixture(scope="module")
def client():
    with httpx.Client(timeout=TIMEOUT) as c:
        yield c


class TestHealthEndpoints:
    """TC-S-01+: Basic server health checks."""

    def test_server_is_up(self, client):
        """TC-S-01: Root endpoint responds (server is running)."""
        r = client.get(f"{BASE}/")
        assert r.status_code in (200, 404), (
            f"Server returned {r.status_code}. Expected 200 or 404 (not 5xx)."
        )

    def test_docs_accessible(self, client):
        """TC-S-02: FastAPI /docs endpoint is accessible."""
        r = client.get(f"{BASE}/docs")
        assert r.status_code == 200, f"/docs returned {r.status_code}"

    def test_cache_refresh_endpoint(self, client):
        """TC-S-03: POST /menu/refresh returns 200 (cache reloads without crash)."""
        r = client.post(f"{BASE}/menu/refresh")
        assert r.status_code == 200, f"/menu/refresh returned {r.status_code}: {r.text[:200]}"


class TestMenuEndpoints:
    """TC-S-10+: Menu structure endpoints."""

    def test_main_menu_returns_items(self, client):
        """TC-S-10: GET /main_design returns at least one menu item."""
        r = client.get(f"{BASE}/main_design")
        assert r.status_code == 200, f"/main_design returned {r.status_code}"
        data = r.json()
        assert len(data) > 0, "Main menu is empty"

    def test_services_overview_endpoint(self, client):
        """TC-S-11: GET /menu/services returns service items."""
        r = client.get(f"{BASE}/menu/services")
        assert r.status_code == 200

    def test_categories_endpoint(self, client):
        """TC-S-12: GET /menu/categories returns category list."""
        r = client.get(f"{BASE}/menu/categories")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0, "No categories returned"

    def test_price_distribution_for_known_service(self, client):
        """TC-S-13: GET /menu/price_distribution returns price for 'Balinese Massage - 60min'."""
        params = {"service_item": "Balinese Massage - 60min"}
        r = client.get(f"{BASE}/menu/price_distribution", params=params)
        assert r.status_code == 200
        data = r.json()
        assert "service_provider_price" in data
        assert data["service_provider_price"] not in (None, "", "0", 0), (
            "Price returned is zero/empty — check 'Final Price (Service Item Button)' column"
        )


class TestDashboardEndpoints:
    """TC-S-20+: Dashboard API endpoints (requires JWT token)."""

    def test_dashboard_stats(self, client):
        """TC-S-20: GET /dashboard-api/stats returns stats object."""
        if not JWT_TOKEN:
            pytest.skip("EASYBALI_JWT_TOKEN not set — skipping auth tests")
        r = client.get(f"{BASE}/dashboard-api/stats", headers=AUTH_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "total_orders" in data or "orders" in data

    def test_customers_endpoint_exists(self, client):
        """TC-S-21: GET /dashboard-api/customers returns 200 (not 404/500)."""
        if not JWT_TOKEN:
            pytest.skip("EASYBALI_JWT_TOKEN not set")
        r = client.get(f"{BASE}/dashboard-api/customers", headers=AUTH_HEADERS)
        assert r.status_code == 200

    def test_customers_search(self, client):
        """TC-S-22: GET /dashboard-api/customers?search=test returns list."""
        if not JWT_TOKEN:
            pytest.skip("EASYBALI_JWT_TOKEN not set")
        r = client.get(f"{BASE}/dashboard-api/customers?search=test", headers=AUTH_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "customers" in data or isinstance(data, list)

    def test_guest_activity_endpoint(self, client):
        """TC-S-23: GET /dashboard-api/activity returns activity list."""
        if not JWT_TOKEN:
            pytest.skip("EASYBALI_JWT_TOKEN not set")
        r = client.get(f"{BASE}/dashboard-api/activity", headers=AUTH_HEADERS)
        assert r.status_code == 200

    def test_issues_endpoint(self, client):
        """TC-S-24: GET /dashboard-api/issues returns issues list."""
        if not JWT_TOKEN:
            pytest.skip("EASYBALI_JWT_TOKEN not set")
        r = client.get(f"{BASE}/dashboard-api/issues", headers=AUTH_HEADERS)
        assert r.status_code == 200

    def test_feedback_endpoint(self, client):
        """TC-S-25: GET /dashboard-api/feedback returns feedback list."""
        if not JWT_TOKEN:
            pytest.skip("EASYBALI_JWT_TOKEN not set")
        r = client.get(f"{BASE}/dashboard-api/feedback", headers=AUTH_HEADERS)
        assert r.status_code == 200


class TestWebhookEndpoints:
    """TC-S-30+: Webhook endpoint sanity (POST structure, not full flow)."""

    def test_xendit_webhook_rejects_invalid_token(self, client):
        """TC-S-30: POST /webhook/xendit-payment rejects missing token with 401/403."""
        r = client.post(
            f"{BASE}/webhook/xendit-payment",
            json={"status": "PAID", "external_id": "booking_TEST001"},
            headers={"x-callback-token": "wrong_token"}
        )
        assert r.status_code in (401, 403, 400), (
            f"Expected auth rejection, got {r.status_code}. "
            "Webhook should reject invalid token."
        )

    def test_whatsapp_webhook_get_verification(self, client):
        """TC-S-31: GET /webhook/whatsapp responds to verification challenge."""
        r = client.get(
            f"{BASE}/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge_123",
                "hub.verify_token": "wrong_token"
            }
        )
        # Either 200 (correct token) or 403 (wrong token) is acceptable — not 500
        assert r.status_code in (200, 403, 400), (
            f"WhatsApp webhook returned {r.status_code} — should not be 5xx"
        )


class TestChatEndpoints:
    """TC-S-40+: Web chatbot endpoint sanity."""

    def test_chatbot_responds_to_hi(self, client):
        """TC-S-40: POST /chatbot/chat responds to 'Hi' with a message."""
        r = client.post(
            f"{BASE}/chatbot/chat",
            json={
                "message": "Hi",
                "user_id": "smoke_test_user",
                "chat_type": "general",
                "language": "EN",
                "villa_code": "WEB_VILLA_01"
            }
        )
        assert r.status_code == 200
        data = r.json()
        assert "response" in data
        assert len(data["response"]) > 0

    def test_currency_chat_mode(self, client):
        """TC-S-41: Currency converter chat mode responds to conversion request."""
        r = client.post(
            f"{BASE}/chatbot/chat",
            json={
                "message": "100 USD to IDR",
                "user_id": "smoke_test_currency",
                "chat_type": "currency-converter",
                "language": "EN",
                "villa_code": "WEB_VILLA_01"
            }
        )
        assert r.status_code == 200
        data = r.json()
        assert "response" in data
        # Response should mention IDR or Rupiah
        response_lower = data["response"].lower()
        assert any(kw in response_lower for kw in ["idr", "rupiah", "indonesian"]), (
            f"Currency converter response doesn't mention IDR: {data['response'][:100]}"
        )
