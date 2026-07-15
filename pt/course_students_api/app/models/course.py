from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CourseStatus:
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=CourseStatus.OPEN)

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")
