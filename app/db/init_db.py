from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Base, Department, Position, Status, Skill, User
from app.db.session import engine
from app.core.security import get_password_hash


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def init_data(session: AsyncSession):
    result = await session.execute(select(Department).limit(1))
    existing_data = result.scalar_one_or_none()

    if existing_data:
        return

    statuses = [
        Status(name="работает"),
        Status(name="в отпуске"),
        Status(name="на больничном"),
        Status(name="в командировке"),
        Status(name="уволен"),
    ]

    departments = [
        Department(name="IT", description="Информационные технологии"),
        Department(name="HR", description="Отдел кадров"),
        Department(name="Finance", description="Финансовый отдел"),
        Department(name="Sales", description="Отдел продаж"),
    ]

    positions = [
        Position(title="Разработчик", description="Backend разработчик", base_salary=100000),
        Position(title="Менеджер проектов", description="Project Manager", base_salary=120000),
        Position(title="HR специалист", description="Специалист по персоналу", base_salary=80000),
        Position(title="Бухгалтер", description="Главный бухгалтер", base_salary=90000),
    ]

    skills = [
        Skill(name="Python", description="Язык программирования Python"),
        Skill(name="FastAPI", description="Фреймворк FastAPI"),
        Skill(name="PostgreSQL", description="База данных PostgreSQL"),
        Skill(name="Docker", description="Контейнеризация"),
        Skill(name="JavaScript", description="Язык программирования JavaScript"),
    ]

    users = [
        User(
            username="admin",
            email="admin@company.com",
            hashed_password=get_password_hash("admin123"),
            is_superuser=True
        ),
        User(
            username="user",
            email="user@company.com",
            hashed_password=get_password_hash("user123"),
            is_superuser=False
        ),
    ]

    for obj in statuses + departments + positions + skills + users:
        session.add(obj)

    await session.commit()


async def init_db():
    await create_tables()

    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await init_data(session)