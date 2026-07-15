from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import build_response
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/{course_id}/students")
def get_course_students(course_id: int, request: Request, db: Session = Depends(get_db)):
    service = CourseService(db)
    result = service.get_course_students(course_id)
    return build_response(
        status_code=200,
        data=result,
        message="Lấy danh sách sinh viên của khóa học thành công",
        request=request,
    )
