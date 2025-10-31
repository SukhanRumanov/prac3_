from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from . import Base


class Status(Base):
    __tablename__ = "status"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)


    employees = relationship("Employee", back_populates="status")

    def __repr__(self):
        return f"Status(id={self.id}, name={self.name})"