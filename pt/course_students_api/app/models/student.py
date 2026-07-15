from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class StudentStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=StudentStatus.ACTIVE)

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")
