from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import Optional

from app.db.session import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.position import Position
from app.models.status import Status
from app.core.security import require_admin

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

    result = await db.execute(
        select(Employee)
        .options(
            joinedload(Employee.department),
            joinedload(Employee.position),
            joinedload(Employee.status)
        )
    )
    employees = result.unique().scalars().all()
    dept_result = await db.execute(select(Department))
    departments = dept_result.scalars().all()

    pos_result = await db.execute(select(Position))
    positions = pos_result.scalars().all()

    status_result = await db.execute(select(Status))
    statuses = status_result.scalars().all()

    return templates.TemplateResponse(
        "edit_employees.html",
        {
            "request": request,
            "employees": employees,
            "departments": departments,
            "positions": positions,
            "statuses": statuses
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

        employee = Employee(
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

        db.add(employee)
        await db.commit()
        await db.refresh(employee)
        logger.info(f"Сотрудник добавлен с ID: {employee.id}")

        return RedirectResponse(url="/web/edit/employees", status_code=303)

    except Exception as e:
        await db.rollback()
        logger.error("ошибка при добавление")
        return RedirectResponse(url=f"/web/edit/employees?error={str(e)}", status_code=303)

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
        result = await db.execute(select(Employee).where(Employee.id == employee_id))
        employee = result.scalar_one_or_none()

        if employee:
            await db.delete(employee)
            await db.commit()
            logger.info("удален работник")

        return RedirectResponse(url="/web/edit/employees", status_code=303)
    except Exception as e:
        logger.error(e)
        await db.rollback()
        return RedirectResponse(url="/web/edit/employees?error=" + str(e), status_code=303)


@router.get("/edit/departments", response_class=HTMLResponse)
async def web_edit_departments(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    result = await db.execute(
        select(
            Department,
            func.count(Employee.id).label('employee_count')
        )
        .outerjoin(Employee, Department.id == Employee.department_id)
        .group_by(Department.id)
    )
    departments_with_count = result.all()
    logger.info("данные изменены")

    departments = []
    for dept, emp_count in departments_with_count:
        departments.append({
            "id": dept.id,
            "name": dept.name,
            "description": dept.description,
            "employee_count": emp_count
        })

    return templates.TemplateResponse(
        "edit_departments.html",
        {
            "request": request,
            "departments": departments
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
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        department = Department(
            name=name,
            description=description
        )

        db.add(department)
        await db.commit()
        await db.refresh(department)
        logger.info("отдел добавлен")

        return RedirectResponse(url="/web/edit/departments", status_code=303)
    except Exception as e:
        logger.error("ошибка в добавление")
        await db.rollback()
        return RedirectResponse(url="/web/edit/departments?error=" + str(e), status_code=303)


@router.post("/edit/departments/delete/{department_id}")
async def web_delete_department(
        department_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_admin)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=302)

    try:
        result = await db.execute(
            select(func.count(Employee.id))
            .where(Employee.department_id == department_id)
        )
        emp_count = result.scalar()

        if emp_count > 0:
            return RedirectResponse(
                url=f"/web/edit/departments?error=Cannot delete department with {emp_count} employees",
                status_code=303
            )

        result = await db.execute(select(Department).where(Department.id == department_id))
        department = result.scalar_one_or_none()

        if department:
            await db.delete(department)
            await db.commit()
            logger.info("отдел удален")

        return RedirectResponse(url="/web/edit/departments", status_code=303)
    except Exception as e:
        logger.error("ошибка в удаление отдела")
        await db.rollback()
        return RedirectResponse(url="/web/edit/departments?error=" + str(e), status_code=303)


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
        position = Position(
            title=title,
            description=description,
            base_salary=base_salary
        )

        db.add(position)
        await db.commit()
        await db.refresh(position)
        logger.info("должность добавлена")

        return RedirectResponse(url="/web/edit/positions", status_code=303)
    except Exception as e:
        logger.error(e)
        await db.rollback()
        return RedirectResponse(url="/web/edit/positions?error=" + str(e), status_code=303)


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
        result = await db.execute(
            select(func.count(Employee.id))
            .where(Employee.position_id == position_id)
        )
        emp_count = result.scalar()

        if emp_count > 0:
            return RedirectResponse(
                url=f"/web/edit/positions?error=Cannot delete position with {emp_count} employees",
                status_code=303
            )

        result = await db.execute(select(Position).where(Position.id == position_id))
        position = result.scalar_one_or_none()

        if position:
            await db.delete(position)
            await db.commit()
            logger.info("должность удалена")

        return RedirectResponse(url="/web/edit/positions", status_code=303)
    except Exception as e:
        logger.error(e)
        await db.rollback()
        return RedirectResponse(url="/web/edit/positions?error=" + str(e), status_code=303)


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
        result = await db.execute(
            select(Position).where(Position.id == position_id)
        )
        position = result.scalar_one_or_none()

        if not position:
            return RedirectResponse(url="/web/edit/positions?error=Position not found", status_code=303)

        position.title = title
        position.description = description
        position.base_salary = base_salary

        await db.commit()
        await db.refresh(position)
        logger.info("обновлена информация о должности")

        return RedirectResponse(url="/web/edit/positions", status_code=303)

    except Exception as e:
        logger.error(e)
        await db.rollback()
        return RedirectResponse(url=f"/web/edit/positions?error={str(e)}", status_code=303)
