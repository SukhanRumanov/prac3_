from fastapi import APIRouter, Request, Depends, Form, status, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.position import Position
from app.models.user import User
from app.core.security import (
    get_current_user, require_admin, authenticate_user,
    create_access_token, get_password_hash
)
from app.schemas.auth import UserCreate
from app.schemas.employee import EmployeeSchema
from app.schemas.position import PositionSchema
from app.schemas.department import DepartmentSchema

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/web", tags=["web"])


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
        request: Request,
        response: Response,
        username: str = Form(...),
        password: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })

    token = create_access_token({"sub": user.username})

    response = RedirectResponse(url="/web/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="user", value=token)
    return response


@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register(
        request: Request,
        response: Response,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    try:
        if password != confirm_password:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Passwords do not match"
            })
        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
            is_active=True
        )

        existing_user = await db.execute(select(User).where(User.username == user_data.username))
        if existing_user.scalar_one_or_none():
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Username already exists"
            })

        existing_email = await db.execute(select(User).where(User.email == user_data.email))
        if existing_email.scalar_one_or_none():
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Email already exists"
            })

        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=user_data.is_active,
            is_superuser=False
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        token = create_access_token({"sub": new_user.username})
        response = RedirectResponse(url="/web/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="user", value=token)
        return response

    except Exception as e:
        await db.rollback()
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": f"Registration failed: {str(e)}"
        })


@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="user")
    return response


@router.get("/")
async def web_root(
        request: Request,
        current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user,
        "is_admin": current_user.is_superuser
    })


@router.get("/employees")
async def web_employees(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Employee))
    employees = result.scalars().all()

    employee_data = []
    for emp in employees:
        department_name = None
        if emp.department_id:
            dept_result = await db.execute(select(Department).where(Department.id == emp.department_id))
            department = dept_result.scalar_one_or_none()
            department_name = department.name if department else None

        position_title = None
        if emp.position_id:
            pos_result = await db.execute(select(Position).where(Position.id == emp.position_id))
            position = pos_result.scalar_one_or_none()
            position_title = position.title if position else None

        employee_schema = EmployeeSchema.from_orm(emp)

        employee_data.append({
            "id": employee_schema.id,
            "first_name": employee_schema.first_name,
            "last_name": employee_schema.last_name,
            "middle_name": employee_schema.middle_name,
            "birth_date": employee_schema.birth_date,
            "email": employee_schema.email,
            "phone": employee_schema.phone,
            "hire_date": employee_schema.hire_date,
            "salary": float(employee_schema.salary),
            "rate": employee_schema.rate,
            "department_id": employee_schema.department_id,
            "position_id": employee_schema.position_id,
            "status_id": employee_schema.status_id,
            "address": employee_schema.address,
            "department_name": department_name,
            "position_title": position_title,
            "full_name": f"{employee_schema.last_name} {employee_schema.first_name} {employee_schema.middle_name or ''}".strip(),
            "age": (date.today() - employee_schema.birth_date).days // 365,
            "work_experience": (date.today() - employee_schema.hire_date).days // 365
        })

    return templates.TemplateResponse("employees.html", {
        "request": request,
        "employees": employee_data,
        "current_user": current_user,
        "is_admin": current_user.is_superuser
    })


@router.get("/departments")
async def web_departments(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Department))
    departments = result.scalars().all()

    departments_data = []
    for dept in departments:
        employee_count_result = await db.execute(
            select(func.count(Employee.id)).where(Employee.department_id == dept.id)
        )
        employee_count = employee_count_result.scalar()

        department_schema = DepartmentSchema(
            id=dept.id,
            name=dept.name,
            description=dept.description,
            employee_count=employee_count
        )

        departments_data.append({
            "id": department_schema.id,
            "name": department_schema.name,
            "description": department_schema.description,
            "employee_count": department_schema.employee_count
        })

    return templates.TemplateResponse("departments.html", {
        "request": request,
        "departments": departments_data,
        "current_user": current_user,
        "is_admin": current_user.is_superuser
    })

@router.get("/positions")
async def web_positions(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Position))
    positions = result.scalars().all()

    positions_data = []
    for pos in positions:
        employee_count_result = await db.execute(
            select(func.count(Employee.id)).where(Employee.position_id == pos.id)
        )
        employee_count = employee_count_result.scalar()

        position_schema = PositionSchema(
            id=pos.id,
            title=pos.title,
            description=pos.description,
            base_salary=pos.base_salary,
            employee_count=employee_count
        )

        positions_data.append({
            "id": position_schema.id,
            "title": position_schema.title,
            "description": position_schema.description,
            "base_salary": float(position_schema.base_salary),
            "employee_count": position_schema.employee_count
        })

    return templates.TemplateResponse("positions.html", {
        "request": request,
        "positions": positions_data,
        "current_user": current_user,
        "is_admin": current_user.is_superuser
    })
