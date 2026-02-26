import asyncio
from httpx import AsyncClient
from main import app

async def test_app():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/currency-converter/chat?user_id=tester",
            json={"query": "convert 2000 US Dollars to INR", "language": "EN"}
        )
        print("Status:", response.status_code)
        print("Body:", response.text)

if __name__ == "__main__":
    asyncio.run(test_app())
