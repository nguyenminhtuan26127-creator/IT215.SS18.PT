"""
Phần 1: Phân tích và đề xuất đa giải pháp cấu hình
6.1. Phân tích truy xuất quan hệ
Vai trò của ForeignKey trong quan hệ N-N:
ForeignKey không thể đặt trực tiếp ở Student hoặc Course vì một sinh viên có thể liên kết với nhiều khóa học và ngược lại — một cột FK chỉ lưu được một giá trị duy nhất, không thể biểu diễn quan hệ nhiều-nhiều. Do đó bắt buộc phải có bảng trung gian (Enrollment) chứa 2 khóa ngoại:

student_id → trỏ đến students.id
course_id → trỏ đến courses.id

Mỗi dòng trong Enrollment đại diện cho một "cặp" liên kết cụ thể giữa 1 sinh viên và 1 khóa học, nhờ đó quan hệ N-N được phân rã thành 2 quan hệ 1-N (Student 1-N Enrollment, Course 1-N Enrollment).
Về back_populates:
back_populates không bắt buộc phải trùng tên bảng trong database. Bản chất của tham số này là khai báo tên thuộc tính Python ở phía đối diện (ở tầng ORM, không liên quan gì đến tên cột/bảng SQL). Nó chỉ đóng vai trò báo cho SQLAlchemy biết: "thuộc tính A ở model này và thuộc tính B ở model kia là hai mặt của cùng một quan hệ", để khi thay đổi một phía thì phía còn lại tự động đồng bộ trong session (không cần query lại DB). Tên gọi hoàn toàn tùy ý, miễn là khớp chính xác giữa 2 model.
6.2. Đề xuất hai giải pháp cấu hình Model
Giải pháp 1 — dùng secondary:
Khai báo trực tiếp relationship giữa Student và Course, truyền bảng Enrollment (hoặc Enrollment.__table__) vào tham số secondary. SQLAlchemy tự động sinh câu JOIN qua bảng trung gian ở tầng ngầm định, lập trình viên chỉ thao tác với student.courses / course.students như một list object bình thường, không cần biết đến sự tồn tại của Enrollment khi truy vấn.
Giải pháp 2 — hai quan hệ 1-N song song:
Không dùng secondary. Thiết lập:

Student.enrollments ↔ Enrollment.student (1-N)
Course.enrollments ↔ Enrollment.course (1-N)

Khi cần lấy danh sách sinh viên của 1 khóa học, phải viết vòng lặp: [e.student for e in course.enrollments]. Giải pháp này giữ được quyền truy cập vào các cột phụ của Enrollment (ví dụ enrolled_date, grade... nếu có), nhưng tốn thêm bước trung gian khi truy xuất.
6.3. Bảng so sánh
Tiêu chíGiải pháp 1 (secondary)Giải pháp 2 (2 quan hệ 1-N)Độ ngắn gọn của codeNgắn gọn, ít khai báo relationship hơnDài hơn, cần khai báo relationship ở cả 2 chiều cho EnrollmentTruy xuất course.studentsGọi thẳng course.students, trả về list StudentKhông có sẵn; phải duyệt [e.student for e in course.enrollments]Độ phức tạp khi đọc code (người mới)Dễ hiểu, trực quan như quan hệ N-N thông thườngKhó hơn vì phải hiểu cơ chế 2 tầng 1-N
Nhận xét:

Giải pháp 1 giúp truy xuất ngắn gọn hơn hẳn (course.students thay vì vòng lặp).
Tuy nhiên, theo nội dung slide đã học (khi bảng trung gian chỉ chứa 2 FK thuần túy, không có cột dữ liệu bổ sung), giải pháp 2 (2 quan hệ 1-N tường minh) mới là giải pháp được khuyến khích, vì nó thể hiện đúng bản chất bảng trung gian như một entity độc lập, dễ mở rộng thêm cột sau này (ví dụ enrolled_date), và là cách tiếp cận chuẩn mực để dạy tư duy ORM cho người mới.

6.4. Lựa chọn giải pháp
Em chọn Giải pháp 2 — hai quan hệ 1-N song song để triển khai source code, vì:

Enrollment được thiết kế là một Model độc lập có id riêng (Primary Key), không phải chỉ là bảng liên kết thuần túy → phù hợp bản chất để expose thành entity với relationship 1-N tường minh.
Dễ mở rộng: nếu sau này cần thêm cột như enrolled_date, status vào Enrollment, cấu trúc hiện tại không cần thay đổi gì.
Tường minh, đúng với cách tiếp cận association object pattern mà slide đã hướng dẫn.

6.5. Các bước thiết kế

Import Base, Mapped, mapped_column, relationship, ForeignKey từ SQLAlchemy 2.0.
Khai báo class Student kế thừa Base, định nghĩa cột id, full_name, email.
Khai báo class Course kế thừa Base, định nghĩa cột id, name.
Khai báo class Enrollment kế thừa Base, định nghĩa id (PK), student_id (FK → students.id), course_id (FK → courses.id).
Thêm relationship("Enrollment", back_populates="student") vào Student (thuộc tính enrollments).
Thêm relationship("Enrollment", back_populates="course") vào Course (thuộc tính enrollments).
Thêm 2 relationship ở Enrollment trỏ ngược lại Student và Course, tương ứng back_populates="enrollments".
Kiểm tra khớp tên back_populates giữa 2 phía của từng cặp quan hệ.
"""


from typing import List
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))

    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="student")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="course")

    @property
    def students(self) -> List[Student]:
        return [e.student for e in self.enrollments]


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")