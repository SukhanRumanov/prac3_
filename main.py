import asyncio
from app.db.init_db import init_db


async def main():
    print("Запуск инициализации базы данных...")

    try:
        await init_db()
        print("База данных успешно инициализирована!")
        print("Созданы таблицы: department, position, status, skill, employee, user")
        print("Добавлены начальные данные")

    except Exception as e:
        print(f"Ошибка при инициализации БД: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())