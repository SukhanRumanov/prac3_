from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from . import Base

employee_skill = Table(
    "employee_skill",
    Base.metadata,
    Column("employee_id", Integer, ForeignKey("employee.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skill.id"), primary_key=True),
)


class Skill(Base):
    __tablename__ = "skill"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    employees = relationship("Employee", secondary=employee_skill, back_populates="skills")

    def __repr__(self):
        return f"Skill(id={self.id}, name={self.name})"