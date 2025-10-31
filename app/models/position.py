from sqlalchemy import Column, Integer, String, Text, Numeric
from sqlalchemy.orm import relationship
from . import Base


class Position(Base):
    __tablename__ = "position"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    base_salary = Column(Numeric(10, 2), nullable=False)

    employees = relationship("Employee", back_populates="position")

    def __repr__(self):
        return f"Position(id={self.id}, title={self.title})"