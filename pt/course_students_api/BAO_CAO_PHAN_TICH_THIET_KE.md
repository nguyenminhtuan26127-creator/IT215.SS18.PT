# BÁO CÁO: API GET /courses/{course_id}/students

## PHẦN 1: PHÂN TÍCH VÀ ĐỀ XUẤT ĐA GIẢI PHÁP

### 1.1. Phân tích đầu vào và đầu ra

**Dữ liệu nào phải được kiểm tra đầu tiên?**
`course_id` phải được kiểm tra tồn tại trước tiên — nếu khóa học không tồn tại thì trả `404` ngay, không cần truy vấn tiếp `Enrollment` hay `Student`.

**Điều kiện lọc Enrollment**
- `Enrollment.course_id == course_id`
- `Enrollment.status IN ('STUDYING', 'COMPLETED')` (loại `CANCELLED`)

**Điều kiện lọc Student**
- `Student.status == 'ACTIVE'` (loại sinh viên `INACTIVE` dù có enrollment hợp lệ)

**Loại bỏ sinh viên trùng**
Một sinh viên có thể có nhiều bản ghi `Enrollment` hợp lệ cho cùng một khóa học (ví dụ dữ liệu lịch sử). Dùng `DISTINCT` trên tập kết quả `Student` (hoặc `GROUP BY Student.id`) để mỗi sinh viên chỉ xuất hiện một lần.

**Trường hợp trả về danh sách rỗng**
- Khóa học tồn tại nhưng chưa có `Enrollment` nào.
- Khóa học có `Enrollment` nhưng tất cả đều `CANCELLED`.
- Khóa học có `Enrollment` hợp lệ nhưng toàn bộ sinh viên liên quan đều `INACTIVE`.

Lưu ý: các trường hợp trên **đều trả `200` với `students: []`**, chỉ trả `404` khi bản thân khóa học không tồn tại.

### 1.2. Đề xuất hai giải pháp

**Giải pháp 1 — Truy vấn Enrollment rồi dùng vòng lặp**
```python
enrollments = db.query(Enrollment).filter(
    Enrollment.course_id == course_id,
    Enrollment.status.in_(["STUDYING", "COMPLETED"])
).all()

seen_ids = set()
students = []
for e in enrollments:
    student = db.query(Student).filter(
        Student.id == e.student_id,
        Student.status == "ACTIVE"
    ).first()
    if student and student.id not in seen_ids:
        seen_ids.add(student.id)
        students.append(student)

students.sort(key=lambda s: s.full_name)
```
Mỗi enrollment phát sinh một câu query `Student` riêng → kinh điển của vấn đề **N+1 query**.

**Giải pháp 2 — JOIN giữa Student và Enrollment**
```python
stmt = (
    select(Student)
    .join(Enrollment, Enrollment.student_id == Student.id)
    .where(
        Enrollment.course_id == course_id,
        Enrollment.status.in_(["STUDYING", "COMPLETED"]),
        Student.status == "ACTIVE",
    )
    .distinct()
    .order_by(Student.full_name.asc())
)
students = db.execute(stmt).scalars().all()
```
Toàn bộ việc lọc, loại trùng (`DISTINCT`), sắp xếp (`ORDER BY`) do MySQL xử lý trong **một câu truy vấn duy nhất**.

## PHẦN 2: SO SÁNH VÀ LỰA CHỌN

### 2.1. Bảng so sánh

| Tiêu chí | Vòng lặp | JOIN |
|---|---|---|
| Độ dễ hiểu | Dễ đọc từng bước, gần với tư duy thủ tục | Cần hiểu SQL JOIN, nhưng logic tập trung, gọn |
| Số câu truy vấn | 1 (Enrollment) + N (Student theo từng enrollment) = N+1 | 1 duy nhất |
| Tốc độ khi dữ liệu nhỏ | Chấp nhận được, khác biệt không đáng kể | Nhanh, không khác biệt lớn |
| Tốc độ khi dữ liệu lớn | Chậm rõ rệt do N+1 query, round-trip DB nhiều lần | Nhanh, DB tối ưu JOIN + index tốt hơn Python loop |
| Bộ nhớ sử dụng | Load nhiều đối tượng trung gian, set kiểm tra trùng ở tầng Python | DB xử lý DISTINCT, ứng dụng chỉ nhận kết quả cuối |
| Khả năng bảo trì | Logic lọc/loại trùng/sắp xếp nằm rải rác trong Python, dễ phát sinh bug | Toàn bộ điều kiện nằm trong 1 câu query, dễ kiểm soát |
| Khả năng mở rộng | Thêm điều kiện lọc phải sửa vòng lặp, dễ tăng thêm số query | Chỉm cần thêm `.where()`, không tăng số câu truy vấn |

### 2.2. Phân tích

- **Dễ hiểu hơn với người mới:** giải pháp vòng lặp, vì đọc tuần tự như if/for thông thường không cần biết SQL JOIN.
- **Tạo nhiều câu truy vấn hơn:** giải pháp vòng lặp (N+1).
- **1.000 sinh viên:** giải pháp JOIN phù hợp hơn hẳn — vòng lặp sẽ gửi khoảng 1.000 câu query riêng lẻ tới MySQL, độ trễ mạng (round-trip) nhân lên rất lớn.
- **Dễ thêm điều kiện lọc hơn:** giải pháp JOIN — chỉ thêm một `.where()`, không phải viết lại logic lọc trong Python.
- **Nguy cơ gây chậm API:** giải pháp vòng lặp, đặc biệt khi số lượng enrollment tăng theo thời gian.

### 2.3. Lựa chọn giải pháp

**Chọn: Giải pháp 2 — JOIN.**

**Lý do:** API này gắn với dữ liệu sẽ tăng dần theo thời gian (số lượng enrollment tích lũy qua nhiều khóa/nhiều học kỳ), nên hiệu năng khi dữ liệu lớn là ưu tiên. JOIN vừa giảm số round-trip DB xuống còn 1, vừa để MySQL (được tối ưu cho việc này, có thể dùng index trên `course_id`, `status`) đảm nhiệm việc lọc/loại trùng/sắp xếp thay vì Python.

**Bối cảnh giải pháp vòng lặp còn phù hợp:** khi logic lọc quá phức tạp để diễn đạt bằng SQL thuần (ví dụ cần gọi thêm service ngoài, tính toán phức tạp theo từng bản ghi), hoặc khi dạy người mới học ORM ở bước đầu và ưu tiên tính trực quan hơn hiệu năng.

**Đánh đổi khi chọn JOIN:** code SQL/ORM ban đầu khó đọc hơn với người chưa quen `join()`/`distinct()`, và việc debug từng bước (in ra kết quả trung gian) khó hơn so với vòng lặp — phải EXPLAIN câu query nếu cần tối ưu thêm.

## PHẦN 3: THIẾT KẾ VÀ TRIỂN KHAI

### 3.1. Các bước thực hiện

```
1. Nhận request GET /courses/{course_id}/students
2. Truy vấn Course theo course_id
   ├─ Không tồn tại → trả 404 "Khóa học không tồn tại"
   └─ Tồn tại → tiếp tục bước 3
3. Thực hiện JOIN Student + Enrollment với điều kiện:
   - Enrollment.course_id = course_id
   - Enrollment.status IN (STUDYING, COMPLETED)
   - Student.status = ACTIVE
   DISTINCT theo Student, ORDER BY full_name ASC
4. Đếm total_students = độ dài danh sách kết quả
5. Trả về 200 với { course_id, course_name, total_students, students[] }
```

### 3.2. Cấu trúc source code

```
app/
  main.py                 # khởi tạo FastAPI, đăng ký router + exception handler
  database.py              # engine, SessionLocal, get_db()
  models/
    student.py
    course.py
    enrollment.py
  schemas/
    course.py              # CourseStudentsResponse, StudentBrief
  services/
    course_service.py      # CourseService.get_course_students() - giải pháp JOIN
  routers/
    course_router.py       # GET /courses/{course_id}/students
  core/
    response.py             # build_response() - format 6 trường chuẩn
    exceptions.py            # global exception handler
```

### 3.3. Cách chạy

```
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Tạo database MySQL tên `course_db` (hoặc sửa `DATABASE_URL` trong `app/database.py`), bảng sẽ tự tạo khi khởi động server.

### 3.4. Đã kiểm thử

Đã test bằng SQLite in-memory với các tình huống:
- Khóa học có 5 sinh viên đăng ký nhưng 1 `INACTIVE`, 1 `CANCELLED`, 1 sinh viên có 2 bản ghi enrollment hợp lệ (trùng) → kết quả đúng 3 sinh viên duy nhất, sắp xếp theo tên tăng dần.
- Khóa học tồn tại nhưng chưa có sinh viên → `200`, `total_students: 0`, `students: []`.
- Khóa học không tồn tại → `404`.

Kết quả JSON khớp đúng định dạng đầu ra mong đợi trong đề bài.
