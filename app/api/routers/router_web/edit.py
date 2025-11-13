from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import Optional
from app.schemas.employee import EmployeeCreate

from app.db.session import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.position import Position
from app.models.status import Status
from app.core.security import require_admin
from app.services.department_service import DepartmentService, DepartmentCreate
from app.services.employee_service import EmployeeService
from app.services.position_service import PositionService, PositionUpdate, PositionCreate

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

from app.logger.logger import setup_logger

logger = setup_logger(__name__)

@router.get("/edit", response_class=HTMLResponse)
async def web_edit(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)


    return templates.TemplateResponse("edit_main.html", {"request": request})


@router.get("/edit/employees", response_class=HTMLResponse)
async def web_edit_employees(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        employee_service = EmployeeService(db)
        employees_data = await employee_service.get_employees_for_web()

        department_service = DepartmentService(db)
        departments_result = await department_service.get_all_departments(skip=0, limit=1000)
        departments = departments_result.payload if departments_result.payload else []

        pos_result = await db.execute(select(Position))
        positions = pos_result.scalars().all()

        status_result = await db.execute(select(Status))
        statuses = status_result.scalars().all()

        logger.info(f"Загружено {len(employees_data)} сотрудников, {len(departments)} отделов, {len(positions)} должностей, {len(statuses)} статусов")

        return templates.TemplateResponse(
            "edit_employees.html",
            {
                "request": request,
                "employees": employees_data,
                "departments": departments,
                "positions": positions,
                "statuses": statuses
            }
        )

    except Exception as e:
        logger.error(f"Ошибка при загрузке страницы редактирования сотрудников: {str(e)}")
        return templates.TemplateResponse(
            "edit_employees.html",
            {
                "request": request,
                "employees": [],
                "departments": [],
                "positions": [],
                "statuses": [],
                "error": "Ошибка при загрузке данных"
            }
        )

@router.post("/edit/employees/add")
async def web_add_employee(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    middle_name: str = Form(None),
    email: str = Form(...),
    phone: str = Form(None),
    birth_date: str = Form(...),
    hire_date: str = Form(...),
    salary: float = Form(...),
    rate: float = Form(default=1.0),
    department_id: int = Form(None),
    position_id: int = Form(None),
    status_id: int = Form(...),
    address: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
        hire_date_obj = datetime.strptime(hire_date, "%Y-%m-%d").date()

        employee_data = EmployeeCreate(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            birth_date=birth_date_obj,
            email=email,
            phone=phone,
            hire_date=hire_date_obj,
            salary=salary,
            rate=rate,
            department_id=department_id,
            position_id=position_id,
            status_id=status_id,
            address=address
        )

        employee_service = EmployeeService(db)
        result = await employee_service.create_employee(employee_data)

        if result.error:
            logger.warning(f"Ошибка при добавлении сотрудника: {result.message}")
            return RedirectResponse(
                url=f"/web/edit/employees?error={result.message}",
                status_code=303
            )

        logger.info(f"Сотрудник добавлен с ID: {result.payload.id if result.payload else 'unknown'}")
        return RedirectResponse(url="/web/edit/employees", status_code=303)

    except Exception as e:
        logger.error(f"Неожиданная ошибка при добавлении сотрудника: {str(e)}")
        return RedirectResponse(
            url=f"/web/edit/employees?error=Unexpected error: {str(e)}",
            status_code=303
        )

@router.post("/edit/employees/delete/{employee_id}")
async def web_delete_employee(
    employee_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        employee_service = EmployeeService(db)
        result = await employee_service.delete_employee(employee_id)

        if result.error:
            logger.warning(f"Ошибка при удалении сотрудника {employee_id}: {result.message}")
            return RedirectResponse(
                url=f"/web/edit/employees?error={result.message}",
                status_code=303
            )

        logger.info(f"Успешно удален сотрудник ID {employee_id}")
        return RedirectResponse(url="/web/edit/employees", status_code=303)

    except Exception as e:
        logger.error(f"Неожиданная ошибка при удалении сотрудника {employee_id}: {str(e)}")
        return RedirectResponse(
            url=f"/web/edit/employees?error=Unexpected error: {str(e)}",
            status_code=303
        )


@router.get("/edit/departments", response_class=HTMLResponse)
async def web_edit_departments(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Попытка доступа к редактированию департаментов без авторизации")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        logger.info(f"Запрос на страницу редактирования департаментов от пользователя: {current_user.username}")

        service = DepartmentService(db)
        departments_data = await service.get_departments_for_web()

        logger.info(f"Успешно загружено {len(departments_data)} департаментов для редактирования")

        return templates.TemplateResponse(
            "edit_departments.html",
            {
                "request": request,
                "departments": departments_data,
                "current_user": current_user
            }
        )

    except Exception as e:
        logger.error(f"Ошибка при загрузке страницы редактирования департаментов: {str(e)}")
        return templates.TemplateResponse(
            "edit_departments.html",
            {
                "request": request,
                "departments": [],
                "current_user": current_user,
                "error": "Произошла ошибка при загрузке данных"
            }
        )


@router.post("/edit/departments/add")
async def web_add_department(
        request: Request,
        name: str = Form(...),
        description: str = Form(None),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Попытка добавления департамента без авторизации")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        logger.info(f"Запрос на добавление департамента '{name}' от пользователя: {current_user.username}")

        department_data = DepartmentCreate(name=name, description=description)

        service = DepartmentService(db)
        result = await service.create_department(department_data)

        if result.error:
            logger.warning(f"Ошибка при добавлении департамента '{name}': {result.message}")
            return RedirectResponse(
                url=f"/web/edit/departments?error={result.message}",
                status_code=303
            )

        logger.info(f"Успешно добавлен департамент: {name} (ID: {result.payload.id})")
        return RedirectResponse(url="/web/edit/departments", status_code=303)

    except Exception as e:
        logger.error(f"Неожиданная ошибка при добавлении департамента '{name}': {str(e)}")
        return RedirectResponse(
            url=f"/web/edit/departments?error=Unexpected error: {str(e)}",
            status_code=303
        )


@router.post("/edit/departments/delete/{department_id}")
async def web_delete_department(
        department_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Попытка удаления департамента без авторизации")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        logger.info(f"Запрос на удаление департамента ID {department_id} от пользователя: {current_user.username}")

        service = DepartmentService(db)
        result = await service.delete_department(department_id)

        if result.error:
            logger.warning(f"Ошибка при удалении департамента ID {department_id}: {result.message}")
            return RedirectResponse(
                url=f"/web/edit/departments?error={result.message}",
                status_code=303
            )

        logger.info(f"Успешно удален департамент ID {department_id}")
        return RedirectResponse(url="/web/edit/departments", status_code=303)

    except Exception as e:
        logger.error(f"Неожиданная ошибка при удалении департамента ID {department_id}: {str(e)}")
        return RedirectResponse(
            url=f"/web/edit/departments?error=Unexpected error: {str(e)}",
            status_code=303
        )

@router.get("/edit/positions", response_class=HTMLResponse)
async def web_edit_positions(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    result = await db.execute(
        select(
            Position,
            func.count(Employee.id).label('employee_count')
        )
        .outerjoin(Employee, Position.id == Employee.position_id)
        .group_by(Position.id)
    )
    positions_with_count = result.all()

    positions = []
    for pos, emp_count in positions_with_count:
        positions.append({
            "id": pos.id,
            "title": pos.title,
            "description": pos.description,
            "base_salary": pos.base_salary,
            "employee_count": emp_count
        })

    logger.info("должность изменена")

    return templates.TemplateResponse(
        "edit_positions.html",
        {
            "request": request,
            "positions": positions
        }
    )


@router.post("/edit/employees/update/{employee_id}")
async def web_update_employee(
        employee_id: int,
        request: Request,
        first_name: str = Form(...),
        last_name: str = Form(...),
        middle_name: str = Form(None),
        email: str = Form(...),
        phone: str = Form(None),
        department_id: int = Form(None),
        position_id: int = Form(None),
        status_id: int = Form(...),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        result = await db.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()

        if not employee:
            return RedirectResponse(url="/web/edit/employees?error=Employee not found", status_code=303)

        employee.first_name = first_name
        employee.last_name = last_name
        employee.middle_name = middle_name
        employee.email = email
        employee.phone = phone
        employee.department_id = department_id
        employee.position_id = position_id
        employee.status_id = status_id

        await db.commit()
        await db.refresh(employee)
        logger.info("обновлена информация о сотруднике")

        return RedirectResponse(url="/web/edit/employees", status_code=303)

    except Exception as e:
        logger.error(e)
        await db.rollback()
        return RedirectResponse(url=f"/web/edit/employees?error={str(e)}", status_code=303)

@router.post("/edit/departments/update/{department_id}")
async def web_update_department(
        department_id: int,
        request: Request,
        name: str = Form(...),
        description: str = Form(None),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        result = await db.execute(
            select(Department).where(Department.id == department_id)
        )
        department = result.scalar_one_or_none()

        if not department:
            return RedirectResponse(url="/web/edit/departments?error=Department not found", status_code=303)

        department.name = name
        department.description = description

        await db.commit()
        await db.refresh(department)
        logger.info("обновлена информация об отделе")

        return RedirectResponse(url="/web/edit/departments", status_code=303)

    except Exception as e:
        logger.error(e)
        await db.rollback()
        return RedirectResponse(url=f"/web/edit/departments?error={str(e)}", status_code=303)

@router.post("/edit/positions/add")
async def web_add_position(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    base_salary: float = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        # Создаем объект PositionCreate для сервиса
        position_data = PositionCreate(
            title=title,
            description=description,
            base_salary=base_salary
        )

        # Используем PositionService для создания должности
        service = PositionService(db)
        result = await service.create_position(position_data)

        if result.error:
            logger.warning(f"Ошибка при добавлении должности '{title}': {result.message}")
            return RedirectResponse(
                url=f"/web/edit/positions?error={result.message}",
                status_code=303
            )

        logger.info(f"Должность добавлена: {title} (ID: {result.payload.id})")
        return RedirectResponse(url="/web/edit/positions", status_code=303)

    except Exception as e:
        logger.error(f"Неожиданная ошибка при добавлении должности '{title}': {str(e)}")
        return RedirectResponse(
            url=f"/web/edit/positions?error=Unexpected error: {str(e)}",
            status_code=303
        )

@router.post("/edit/positions/update/{position_id}")
async def web_update_position(
    position_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    base_salary: float = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        # Создаем объект PositionUpdate для сервиса
        position_data = PositionUpdate(
            title=title,
            description=description,
            base_salary=base_salary
        )

        # Используем PositionService для обновления должности
        service = PositionService(db)
        result = await service.update_position(position_id, position_data)

        if result.error:
            logger.warning(f"Ошибка при обновлении должности ID {position_id}: {result.message}")
            return RedirectResponse(
                url=f"/web/edit/positions?error={result.message}",
                status_code=303
            )

        logger.info(f"Должность обновлена: {title} (ID: {position_id})")
        return RedirectResponse(url="/web/edit/positions", status_code=303)

    except Exception as e:
        logger.error(f"Неожиданная ошибка при обновлении должности ID {position_id}: {str(e)}")
        return RedirectResponse(
            url=f"/web/edit/positions?error=Unexpected error: {str(e)}",
            status_code=303
        )

@router.post("/edit/positions/delete/{position_id}")
async def web_delete_position(
    position_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        # Используем PositionService для удаления должности
        service = PositionService(db)
        result = await service.delete_position(position_id)

        if result.error:
            logger.warning(f"Ошибка при удалении должности ID {position_id}: {result.message}")
            return RedirectResponse(
                url=f"/web/edit/positions?error={result.message}",
                status_code=303
            )

        logger.info(f"Должность удалена: ID {position_id}")
        return RedirectResponse(url="/web/edit/positions", status_code=303)

    except Exception as e:
        logger.error(f"Неожиданная ошибка при удалении должности ID {position_id}: {str(e)}")
        return RedirectResponse(
            url=f"/web/edit/positions?error=Unexpected error: {str(e)}",
            status_code=303
        )
