from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload, joinedload
from app.db.session import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.models.position import Position
from app.models.status import Status
from app.models.skill import Skill
from app.schemas.employee import EmployeeSchema, EmployeeCreate, EmployeeUpdate, EmployeeFilter
from app.api.dependencies import get_current_user_optional, get_current_superuser

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=list[EmployeeSchema])
async def get_employees(
        db: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        department_id: Optional[int] = None,
        position_id: Optional[int] = None,
        status_id: Optional[int] = None,
        search: Optional[str] = None,
):
    query = select(Employee).options(
        selectinload(Employee.department),
        selectinload(Employee.position),
        selectinload(Employee.status),
        selectinload(Employee.skills)
    )

    if department_id:
        query = query.where(Employee.department_id == department_id)
    if position_id:
        query = query.where(Employee.position_id == position_id)
    if status_id:
        query = query.where(Employee.status_id == status_id)
    if search:
        search_filter = or_(
            Employee.first_name.ilike(f"%{search}%"),
            Employee.last_name.ilike(f"%{search}%"),
            Employee.middle_name.ilike(f"%{search}%")
        )
        query = query.where(search_filter)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    employees = result.scalars().all()

    employee_schemas = []
    for emp in employees:
        schema_data = {
            'id': emp.id,
            'first_name': emp.first_name,
            'last_name': emp.last_name,
            'middle_name': emp.middle_name,
            'birth_date': emp.birth_date,
            'email': emp.email,
            'phone': emp.phone,
            'hire_date': emp.hire_date,
            'salary': emp.salary,
            'rate': emp.rate,
            'department_id': emp.department_id,
            'position_id': emp.position_id,
            'status_id': emp.status_id,
            'address': emp.address,
            'full_name': emp.full_name,
            'created_at': emp.created_at,
            'updated_at': emp.updated_at,
        }

        if emp.department:
            schema_data['department_name'] = emp.department.name
        if emp.position:
            schema_data['position_title'] = emp.position.title
        if emp.status:
            schema_data['status_name'] = emp.status.name
        if emp.skills:
            schema_data['skills'] = [skill.name for skill in emp.skills]

        employee_schemas.append(EmployeeSchema(**schema_data))

    return employee_schemas


@router.get("/{employee_id}", response_model=EmployeeSchema)
async def get_employee(employee_id: int, db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(Employee)
        .options(
            selectinload(Employee.department),
            selectinload(Employee.position),
            selectinload(Employee.status),
            selectinload(Employee.skills)
        )
        .where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    schema_data = {
        'id': employee.id,
        'first_name': employee.first_name,
        'last_name': employee.last_name,
        'middle_name': employee.middle_name,
        'birth_date': employee.birth_date,
        'email': employee.email,
        'phone': employee.phone,
        'hire_date': employee.hire_date,
        'salary': employee.salary,
        'rate': employee.rate,
        'department_id': employee.department_id,
        'position_id': employee.position_id,
        'status_id': employee.status_id,
        'address': employee.address,
        'full_name': employee.full_name,
        'created_at': employee.created_at,
        'updated_at': employee.updated_at,
    }

    if employee.department:
        schema_data['department_name'] = employee.department.name
    if employee.position:
        schema_data['position_title'] = employee.position.title
    if employee.status:
        schema_data['status_name'] = employee.status.name
    if employee.skills:
        schema_data['skills'] = [skill.name for skill in employee.skills]

    return EmployeeSchema(**schema_data)


@router.post("/", response_model=EmployeeSchema)
async def create_employee(
        employee_data: EmployeeCreate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    employee = Employee(**employee_data.model_dump())
    db.add(employee)
    await db.commit()
    await db.refresh(employee)

    return await get_employee(employee.id, db)


@router.put("/{employee_id}", response_model=EmployeeSchema)
async def update_employee(
        employee_id: int,
        employee_data: EmployeeUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    result = await db.execute(
        select(Employee)
        .options(
            selectinload(Employee.department),
            selectinload(Employee.position),
            selectinload(Employee.status),
            selectinload(Employee.skills)
        )
        .where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = employee_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)

    return await get_employee(employee_id, db)


@router.delete("/{employee_id}")
async def delete_employee(
        employee_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_superuser)
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    await db.delete(employee)
    await db.commit()

    return {"message": "Employee deleted successfully"}


@router.get("/debug/statuses")
async def debug_statuses(db: AsyncSession = Depends(get_db)):
    from app.models.status import Status
    result = await db.execute(select(Status))
    statuses = result.scalars().all()
    return [{"id": s.id, "name": s.name} for s in statuses]