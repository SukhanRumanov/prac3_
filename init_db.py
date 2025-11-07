import asyncio
from app.db.init_db import init_db
import traceback


async def main():
    try:
        await init_db()
    except Exception as e:
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())