from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.course import Course
from app.models.student import Student, StudentStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.course import StudentBrief, CourseStudentsResponse


class CourseService:
    def __init__(self, db: Session):
        self.db = db

    def get_course_students(self, course_id: int) -> CourseStudentsResponse:
        # 1. Khóa học phải tồn tại -> 404 nếu không có
        course = self.db.execute(
            select(Course).where(Course.id == course_id)
        ).scalar_one_or_none()
        if course is None:
            raise HTTPException(status_code=404, detail="Khóa học không tồn tại")

        # 2. Một câu truy vấn duy nhất: JOIN Student với Enrollment,
        #    lọc đúng trạng thái Enrollment (STUDYING/COMPLETED) và Student (ACTIVE),
        #    loại trùng bằng DISTINCT, sắp xếp theo tên tăng dần.
        stmt = (
            select(Student)
            .join(Enrollment, Enrollment.student_id == Student.id)
            .where(
                Enrollment.course_id == course_id,
                Enrollment.status.in_(
                    [EnrollmentStatus.STUDYING, EnrollmentStatus.COMPLETED]
                ),
                Student.status == StudentStatus.ACTIVE,
            )
            .distinct()
            .order_by(Student.full_name.asc())
        )
        students = self.db.execute(stmt).scalars().all()

        return CourseStudentsResponse(
            course_id=course.id,
            course_name=course.name,
            total_students=len(students),
            students=[StudentBrief.model_validate(s) for s in students],
        )
