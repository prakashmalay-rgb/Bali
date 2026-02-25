import pytest
import httpx
import asyncio
import time
import json

BASE_URL = "http://localhost:8000"
TEST_USER = "test_user_unique_123"

@pytest.mark.asyncio
async def test_sanity_backend():
    """Sanity test: Verify backend is reachable."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/")
            assert response.status_code == 200
        except Exception as e:
            pytest.fail(f"Backend not reachable at {BASE_URL}: {e}")

@pytest.mark.asyncio
async def test_chatbot_functionality():
    """Functionality test: Verify chatbot generates response."""
    async with httpx.AsyncClient() as client:
        payload = {
            "query": "Hello, I want to book a massage",
            "chat_type": "general",
            "language": "EN"
        }
        response = await client.post(
            f"{BASE_URL}/chatbot/generate-response?user_id={TEST_USER}",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0

@pytest.mark.asyncio
async def test_language_relevance():
    """Relevance test: Verify chatbot respects language request."""
    async with httpx.AsyncClient() as client:
        # Test Indonesian
        payload = {
            "query": "Siapa kamu?",
            "chat_type": "general",
            "language": "ID"
        }
        response = await client.post(
            f"{BASE_URL}/chatbot/generate-response?user_id={TEST_USER}",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        # Look for Indonesian keywords
        indonesian_keywords = ["Saya", "Bali", "EASYbali", "bantu"]
        found = any(kw.lower() in data["response"].lower() for kw in indonesian_keywords)
        assert found, f"Response did not appear to be in Indonesian: {data['response']}"

@pytest.mark.asyncio
async def test_load_handling():
    """Load test: Verify response under concurrent requests."""
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(5): # Small load for test sanity
            payload = {"query": f"Query {i}", "chat_type": "general", "language": "EN"}
            tasks.append(client.post(f"{BASE_URL}/chatbot/generate-response?user_id={TEST_USER}_{i}", json=payload))
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        for resp in responses:
            assert resp.status_code == 200
        
        print(f"Total time for 5 concurrent requests: {end_time - start_time:.2f}s")

@pytest.mark.asyncio
async def test_crash_resilience():
    """Crash test: Verify handling of malformed JSON."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/chatbot/generate-response?user_id={TEST_USER}",
            content="invalid-json"
        )
        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

if __name__ == "__main__":
    asyncio.run(test_sanity_backend())
    asyncio.run(test_chatbot_functionality())
