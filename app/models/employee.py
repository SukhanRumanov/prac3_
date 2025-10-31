from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import Base
from .skill import employee_skill


class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)

    # Основная инфа
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)

    # Личная
    birth_date = Column(Date, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), nullable=True)

    # Рабочая
    hire_date = Column(Date, nullable=False)
    salary = Column(Numeric(10, 2), nullable=False)
    rate = Column(Numeric(3, 2), default=1.0)

    # Внешние ключи
    department_id = Column(Integer, ForeignKey("department.id"), index=True, nullable=True)
    position_id = Column(Integer, ForeignKey("position.id"), index=True, nullable=True)
    status_id = Column(Integer, ForeignKey("status.id"), default=1, index=True)

    # Дополнительные поля
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    department = relationship("Department", back_populates="employees")
    position = relationship("Position", back_populates="employees")
    status = relationship("Status", back_populates="employees")
    skills = relationship("Skill", secondary=employee_skill, back_populates="employees")

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

    def __repr__(self):
        return f"Employee(id={self.id}, name={self.full_name})"