import asyncio
import sys
import os

# Add the backend root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.language import optimizer
async def main():
    try:
        res = await optimizer.quantum_response('teststr', 'Hi! I want to learn Bahasa Bali.')
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
