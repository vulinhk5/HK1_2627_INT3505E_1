# Bookstore API 
REST API nhà sách viết bằng Flask + Flask-SQLAlchemy + jsonschema.
- Lab 01: CRUD `books`, kiểm tra dữ liệu bằng JSON Schema, lỗi trả về dạng JSON.
- Lab 02: phân trang `offset` / `cursor`, lọc theo danh mục, sắp xếp.

```text
api_session_05/
├── bookstore-api/   # app.py, models.py, routes/books.py, schemas/book.json, test_books.py, Postman
├── lab01_test/      # ảnh chạy Lab 01
├── lab02_test/      # ảnh chạy Lab 02
└── bai01_resource design/   # thiết kế API đặt phòng khách sạn (PDF + JSON Schema)
```

## Chạy

```powershell
pip install flask flask-sqlalchemy jsonschema pytest
cd bookstore-api
python app.py            # http://127.0.0.1:5000
pytest -v                # 54 test, kết quả: 54 passed
```

Muốn tạo sách cần có danh mục trước (chưa có endpoint tạo Category). 

```powershell
python -c "from app import app; from models import db, Category; ctx = app.app_context(); ctx.push(); db.create_all(); db.session.add_all([Category(name='Programming', slug='programming'), Category(name='Fiction', slug='fiction')]); db.session.commit()"
```
## API
Base: `/api/v1/books`
| Method | URL | Thành công | Lỗi |
|---|---|---|---|
| GET | `/api/v1/books?strategy=offset\|cursor&limit=&offset=&cursor=&sort=&genre=&cat_id=` | 200 | 400 `bad_strategy` / `bad_sort` / `bad_cursor` |
| GET | `/api/v1/books/{id}` | 200 | 404 `not_found` |
| POST | `/api/v1/books` | 201 | 400, 422 `validation_error`, 409 `conflict` |
| PUT | `/api/v1/books/{id}` | 200 | 404, 400, 422, 409 |
| DELETE | `/api/v1/books/{id}` | 204 | 404 |

Lỗi luôn có dạng `{"error": "<mã>", "message": "<mô tả>"}`.

---
## Kết quả chạy Lab 01 

**1. `POST /api/v1/books` tạo "The Ones Who Walk Away from Omelas" → `201 Created`**

![Lab01-1](lab01_test/Screenshot%202026-10-19%20163331.png)

**2. `POST /api/v1/books` tạo "Demian" → `201 Created`**

![Lab01-2](lab01_test/Screenshot%202026-10-19%20164145.png)

**3. `GET /api/v1/books` → `200`, liệt kê `book_1` … `book_6`**

![Lab01-3](lab01_test/Screenshot%202026-10-19%20164321.png)

**4. `GET /api/v1/books/4` → `200 OK`**

![Lab01-4](lab01_test/Screenshot%202026-10-19%20164353.png)

**5. `GET /api/v1/books/1212` → `404 Not Found` (body JSON)**

![Lab01-5](lab01_test/Screenshot%202026-10-19%20164433.png)

**6. `POST` thiếu `title`, giá âm → `422 Unprocessable Entity`**

![Lab01-6](lab01_test/Screenshot%202026-10-19%20164612.png)

**7. Log server khớp các lệnh trên: `201, 201, 201, 200, 200, 404, 422`**

![Lab01-7](lab01_test/Screenshot%202026-10-19%20164930.png)

---

## Kết quả chạy Lab 02 

**1. Khởi động server: `python app.py`**

![Lab02-1](lab02_test/Screenshot%202026-10-19%20181456.png)

**2. Log server của cả phiên test (8 request: 200, 200, 400, 400, 200, 200, 200, 400)**

![Lab02-2](lab02_test/Screenshot%202026-10-19%20193702.png)

**3. `GET ?sort=price` → `200`**

![Lab02-3](lab02_test/Screenshot%202026-10-19%20193925.png)

**4. Hết dữ liệu: `"next_cursor": null`; `GET ?sort=-id` → `200`, `id` giảm dần**

![Lab02-4](lab02_test/Screenshot%202026-10-19%20193930.png)

**5. `GET ?sort=foo` → `400 bad_sort`**

![Lab02-5](lab02_test/Screenshot%202026-10-19%20193934.png)

**6. `GET ?sort=-price&cat_id=1` → `200` (lọc theo danh mục)**

![Lab02-6](lab02_test/Screenshot%202026-10-19%20193937.png)

**7. Kết quả lọc `cat_id=1`, giá giảm dần; sách cùng giá xếp theo `id` giảm dần**

![Lab02-7](lab02_test/Screenshot%202026-10-19%20193948.png)

**8. `GET ?sort=-price&limit=2` → 2 phần tử + `next_cursor`**

![Lab02-8](lab02_test/Screenshot%202026-10-19%20193953.png)

**9. `GET ?sort=-price&limit=2&cursor=…` → `200`**

![Lab02-9](lab02_test/Screenshot%202026-10-19%20193957.png)

**10. `GET ?sort=-price&cursor=abcxyz_invalid` → `400 bad_cursor`**

![Lab02-10](lab02_test/Screenshot%202026-10-19%20194001.png)

---

## Kiểm thử

- **pytest** (`bookstore-api/test_books.py`): 54 test — 15 cho Lab 01 (CRUD và các lỗi 400 / 404 / 409 / 422), 39 cho Lab 02 (offset, cursor, 9 kiểu sort, lọc, lỗi tham số). Kết quả: `54 passed`.
- **Postman** (`bookstore-api.postman_collection.json`): 20 request kèm script kiểm tra; chạy bằng Collection Runner.

