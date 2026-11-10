# Product API – Lab 01

REST API quản lý sản phẩm, tồn kho và đơn hàng, được xây dựng bằng **Flask**, **SQLAlchemy 2.x** và **PostgreSQL**. Dự án có định nghĩa API theo chuẩn OpenAPI 3.0, quản lý thay đổi cơ sở dữ liệu bằng Flask-Migrate/Alembic và kiểm thử bằng pytest.

## 1. Chức năng
### Products

- Tạo, xem danh sách và xem chi tiết sản phẩm.
- Cập nhật một phần thông tin sản phẩm.
- Archive sản phẩm (soft delete); sản phẩm đã archive không còn xuất hiện trong danh sách và được xem như không tồn tại khi truy vấn.
- Đặt trước số lượng sản phẩm trong kho; không cho phép đặt vượt quá số lượng còn lại.
- Phân trang danh sách với `page` và `size`.

### Orders

- Tạo đơn hàng với một hoặc nhiều sản phẩm.
- Xem danh sách và chi tiết đơn hàng.
- Thêm hoặc xóa một dòng sản phẩm trong đơn.
- Lưu `unit_price_cents` tại thời điểm thêm sản phẩm vào đơn, do đó tổng tiền của đơn không thay đổi khi giá sản phẩm được cập nhật về sau.
- Không cho phép một sản phẩm xuất hiện nhiều lần trong cùng một đơn.
- Mỗi đơn phải còn ít nhất một dòng sản phẩm.

**Quy tắc tồn kho:** tạo đơn hàng không tự động trừ tồn kho. Muốn giảm tồn kho, sử dụng endpoint `POST /api/v1/products/{product_id}/reserve`.

## 2. Cấu trúc thư mục

```text
lab01/
├── migrations/                 # Alembic migration scripts
├── openapi/
│   ├── products.yaml           # OpenAPI specification cho Products
│   └── orders.yaml             # OpenAPI specification cho Orders
├── src/
│   └── product_api/
│       ├── api/
│       │   ├── schemas/        # Marshmallow schemas
│       │   ├── errors.py       # Chuẩn hóa lỗi trả về
│       │   ├── health.py       # Liveness/readiness endpoints
│       │   ├── products.py     # Product endpoints
│       │   └── orders.py       # Order endpoints (cần đổi tên file hiện tại)
│       ├── models/             # SQLAlchemy models
│       ├── config.py           # Cấu hình ứng dụng
│       ├── extensions.py       # db và migrate extensions
│       ├── factory.py          # Flask application factory
│       └── logging_config.py   # JSON request logging
├── tests/                      # pytest test suite
├── .env.example                # Mẫu biến môi trường
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml              # Project metadata và dependencies
└── wsgi.py                     # WSGI entry point
```

## 3. Cài đặt và cấu hình

### Yêu cầu

- Python 3.11 trở lên.
- Docker Desktop và Docker Compose (nếu chạy cùng PostgreSQL bằng Docker).
- Git (không bắt buộc, nếu chỉ tải source code về chạy).

### Cấu hình biến môi trường

Tạo file `.env` từ file mẫu `.env.example`:

**Windows PowerShell**
```powershell
Copy-Item .env.example .env
```
### Chạy ứng dụng bằng Docker Compose
```bash
docker compose up --build
```
## 4. Chạy kiểm thử
Cài dependencies phát triển:
pip install -e ".[dev]"
Chạy toàn bộ test suite:
pytest -v
