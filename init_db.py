import asyncio
from app.db.init_db import init_db
import traceback
from app.logger.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    try:
        await init_db()
        logger.info("База данных создана")
    except Exception as e:
        traceback.print_exc()
        logger.info("ошибка в создание базы данных")


if __name__ == "__main__":
    asyncio.run(main())