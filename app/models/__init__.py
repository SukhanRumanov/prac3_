from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .department import Department
from .position import Position
from .status import Status
from .skill import Skill
from .employee import Employee
from .user import User


__all__ = [
    "Base",
    "Department",
    "Position",
    "Status",
    "Skill",
    "Employee",
    "User",
]