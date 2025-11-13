from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.db.session import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.position import Position
from app.models.status import Status
from app.core.security import get_current_user
from app.schemas.employee import EmployeeSchema, EmployeeFilter, EmployeeListResponse
from fastapi import status
templates = Jinja2Templates(directory="app/templates")

from app.services.employee_service import EmployeeService

router = APIRouter()

from app.logger.logger import setup_logger

logger = setup_logger(__name__)

@router.get("/employees")
async def web_employees(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)

    try:
        service = EmployeeService(db)
        employees_data = await service.get_employees_for_web()

        logger.info(f"Успешно выведено {len(employees_data)} сотрудников через сервис")

        return templates.TemplateResponse("employees.html", {
            "request": request,
            "employees": employees_data,
            "current_user": current_user,
            "is_admin": current_user.is_superuser
        })

    except Exception as e:
        logger.error(f"Ошибка при получении сотрудников для веб-интерфейса: {str(e)}")
        return templates.TemplateResponse("employees.html", {
            "request": request,
            "employees": [],
            "current_user": current_user,
            "is_admin": current_user.is_superuser,
            "error": "Ошибка при загрузке данных сотрудников"
        })
@router.get("/employees/filter")
async def web_employees_filter(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)
):
    if current_user is None:
        logger.warning("Not logged in")
        return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)

    try:
        query_params = request.query_params

        filter_data = {}
        if query_params.get("department_id"):
            filter_data["department_id"] = int(query_params.get("department_id"))
        if query_params.get("position_id"):
            filter_data["position_id"] = int(query_params.get("position_id"))
        if query_params.get("status_id"):
            filter_data["status_id"] = int(query_params.get("status_id"))
        if query_params.get("hire_date_from"):
            filter_data["hire_date_from"] = date.fromisoformat(query_params.get("hire_date_from"))
        if query_params.get("hire_date_to"):
            filter_data["hire_date_to"] = date.fromisoformat(query_params.get("hire_date_to"))
        if query_params.get("salary_from"):
            filter_data["salary_from"] = Decimal(query_params.get("salary_from"))
        if query_params.get("salary_to"):
            filter_data["salary_to"] = Decimal(query_params.get("salary_to"))
        if query_params.get("search"):
            filter_data["search"] = query_params.get("search")

        employee_filter = EmployeeFilter(**filter_data)

        page = int(query_params.get("page", 1))
        size = int(query_params.get("size", 20))

        query = select(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.position),
            joinedload(Employee.status)
        )

        filters = []

        if employee_filter.department_id:
            filters.append(Employee.department_id == employee_filter.department_id)
        if employee_filter.position_id:
            filters.append(Employee.position_id == employee_filter.position_id)
        if employee_filter.status_id:
            filters.append(Employee.status_id == employee_filter.status_id)
        if employee_filter.hire_date_from:
            filters.append(Employee.hire_date >= employee_filter.hire_date_from)
        if employee_filter.hire_date_to:
            filters.append(Employee.hire_date <= employee_filter.hire_date_to)
        if employee_filter.salary_from:
            filters.append(Employee.salary >= float(employee_filter.salary_from))
        if employee_filter.salary_to:
            filters.append(Employee.salary <= float(employee_filter.salary_to))
        if employee_filter.search:
            search_term = f"%{employee_filter.search}%"
            filters.append(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.middle_name.ilike(search_term)
                )
            )

        if filters:
            query = query.where(and_(*filters))

        count_query = select(func.count()).select_from(Employee)
        if filters:
            count_query = count_query.where(and_(*filters))

        total_count = (await db.execute(count_query)).scalar()

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        employees = (await db.execute(query)).unique().scalars().all()

        employee_schemas = [EmployeeSchema.from_orm(emp) for emp in employees]
        total_pages = (total_count + size - 1) // size if total_count > 0 else 1

        employee_list_response = EmployeeListResponse(
            items=employee_schemas,
            total=total_count,
            page=page,
            size=size,
            pages=total_pages
        )

        departments = (await db.execute(select(Department))).scalars().all()
        positions = (await db.execute(select(Position))).scalars().all()
        statuses = (await db.execute(select(Status))).scalars().all()

        employee_data = []
        for emp_schema in employee_list_response.items:
            emp_obj = next((emp for emp in employees if emp.id == emp_schema.id), None)
            employee_data.append({
                "id": emp_schema.id,
                "full_name": f"{emp_schema.last_name} {emp_schema.first_name} {emp_schema.middle_name or ''}".strip(),
                "email": emp_schema.email,
                "phone": emp_schema.phone,
                "hire_date": emp_schema.hire_date,
                "salary": float(emp_schema.salary),
                "department_name": emp_obj.department.name if emp_obj and emp_obj.department else "-",
                "position_title": emp_obj.position.title if emp_obj and emp_obj.position else "-",
                "status_name": emp_obj.status.name if emp_obj and emp_obj.status else "-"
            })

        return templates.TemplateResponse("employees_filter.html", {
            "request": request,
            "employees": employee_data,
            "departments": departments,
            "positions": positions,
            "statuses": statuses,
            "current_user": current_user,
            "page": employee_list_response.page,
            "size": employee_list_response.size,
            "total": employee_list_response.total,
            "pages": employee_list_response.pages,
            "filters": employee_filter.model_dump()
        })

    except Exception as e:
        logger.error(e)
        return RedirectResponse(url="/web/employees?error=" + str(e), status_code=303)