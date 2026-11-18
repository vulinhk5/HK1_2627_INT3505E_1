# Tasks API — SOA Buổi 04 (OpenAPI và Flask)

API quản lý task nội bộ: đặc tả **OpenAPI 3.0.3** (`tasks.yaml`) và bản cài đặt bằng **Flask** (`app.py`, dữ liệu lưu trong bộ nhớ). Tài liệu được hiển thị bằng **Swagger UI**.

```text
api_session_04/
├── tasks.yaml   # đặc tả OpenAPI 3.0.3
├── app.py       # server Flask
└── result/      # 12 ảnh Swagger UI
```

## Chạy

```powershell
pip install flask pyjwt
python app.py                         # http://127.0.0.1:5000/v1
$env:JWT_SECRET = "<khóa>"; python app.py   # bật kiểm tra chữ ký JWT (HS256)
```

Biến môi trường tùy chọn: `HOST`, `PORT`, `FLASK_DEBUG=1`. Swagger UI (`index.html` trỏ tới `./tasks.yaml`) mở bằng Live Server tại `http://127.0.0.1:5500/index.html`.

```powershell
curl.exe -X POST http://127.0.0.1:5000/v1/tasks -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" -d '{\"title\": \"Review code module Auth\", \"priority\": \"medium\", \"dueDate\": \"2026-09-20\"}'
```

## API

Base: `http://localhost:5000/v1` · Xác thực: `Authorization: Bearer <JWT>` cho mọi endpoint.

| Method | URL | Mô tả | Thành công | Lỗi |
|---|---|---|---|---|
| GET | `/v1/tasks?status=` | Danh sách task, lọc theo `todo` / `in_progress` / `done` | 200 | 401 |
| POST | `/v1/tasks` | Tạo task (chỉ `title` bắt buộc), trả header `Location` | 201 | 401, 422 |
| GET | `/v1/tasks/{taskId}` | Chi tiết một task | 200 | 401, 404 |
| PATCH | `/v1/tasks/{taskId}` | Cập nhật một phần, phải gửi ít nhất một field | 200 | 401, 404, 422 |
| DELETE | `/v1/tasks/{taskId}` | Xóa task | 204 | 401, 404 |

Task gồm `id` (UUID), `title` (1–200 ký tự), `status` (mặc định `todo`), `priority` (`low` / `medium` / `high`, mặc định `medium`), `dueDate` (`YYYY-MM-DD` hoặc `null`), `assigneeId` (UUID hoặc `null`), `createdAt`, `updatedAt`. Lỗi có dạng `{"code", "message", "details": [{"field", "issue"}]}`.

---

## Ảnh Swagger UI

**1. Swagger UI nạp `tasks.yaml`: Tasks API 1.0.0 (OAS 3.0), server `http://localhost:5000/v1`, nút Authorize (Bearer JWT), `GET /tasks` có tham số lọc `status`**

![Tổng quan](result/Screenshot%202026-10-07%20121734.png)

**2. `GET /tasks`: response `200` (mảng task) và `401`**

![GET /tasks 200 và 401](result/Screenshot%202026-10-07%20121520.png)

**3. `GET /tasks`: phần còn lại của response `401`**

![GET /tasks 401](result/Screenshot%202026-10-07%20121533.png)

**4. `POST /tasks`: request body bắt buộc, ví dụ `{title, priority, dueDate}`**

![POST /tasks request body](result/Screenshot%202026-10-07%20121538.png)

**5. `POST /tasks`: `201` tạo thành công, body là Task, header `Location: /v1/tasks/{id}`; kèm `401`**

![POST /tasks 201](result/Screenshot%202026-10-07%20121549.png)

**6. `POST /tasks`: `422` dữ liệu không hợp lệ; bắt đầu `GET /tasks/{taskId}` với `taskId` kiểu UUID**

![POST 422 và GET theo id](result/Screenshot%202026-10-07%20121554.png)

**7. `GET /tasks/{taskId}`: `200` chi tiết task và `401`**

![GET /tasks/{taskId} 200](result/Screenshot%202026-10-07%20121601.png)

**8. `GET /tasks/{taskId}`: `404` không tìm thấy; bắt đầu `PATCH /tasks/{taskId}`**

![GET 404 và PATCH](result/Screenshot%202026-10-07%20121605.png)

**9. `PATCH`: request body `{"status": "done"}`, `200` trả task sau cập nhật (`status` là `done`)**

![PATCH 200](result/Screenshot%202026-10-07%20121612.png)

**10. `PATCH`: các response `401`, `404`, `422`**

![PATCH 401 404 422](result/Screenshot%202026-10-07%20121617.png)

**11. `PATCH`: `422`; bắt đầu `DELETE /tasks/{taskId}`**

![PATCH 422 và DELETE](result/Screenshot%202026-10-07%20121620.png)

**12. `DELETE`: `204` xóa thành công (không có body), `401`, `404`**

![DELETE 204](result/Screenshot%202026-10-07%20121625.png)

---

## Ghi chú

- Ảnh chụp giao diện tài liệu Swagger UI dựng từ `tasks.yaml`; chưa có ảnh gọi thật tới server Flask.
- Ví dụ lỗi `401`, `404`, `422` trong ảnh đều hiện `VALIDATION_ERROR` vì dùng chung schema `Error` với một ví dụ cố định.
- Không đặt `JWT_SECRET` thì server chấp nhận mọi Bearer token không rỗng (chỉ dùng để demo). Dữ liệu mất khi khởi động lại.
- `app.py` chưa bật CORS nên "Try it out" từ Swagger UI (cổng 5500) sang Flask (cổng 5000) sẽ bị trình duyệt chặn; dùng curl hoặc thêm `flask-cors`.
