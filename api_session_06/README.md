# Social Network API — SOA Buổi 06 (Thiết kế API theo OpenAPI và bảo mật)

Thiết kế API mạng xã hội theo hướng **design-first**: viết đặc tả **OpenAPI 3.0.3** cho 3 endpoint (đăng nhập, làm mới token, xem bài viết), chạy thử bằng **mock server Prism** và kiểm tra trên **Swagger UI**. Kèm bản rà soát bảo mật cho 3 endpoint này.

```text
api_session_06/
├── socialNetwork.yaml   # đặc tả OpenAPI 3.0.3
├── SecurityAudit.md     # 9 điểm có thể lộ thông tin và cách giảm thiểu
├── app.py               # trống: chưa cài đặt server thật, dùng mock
└── test/                # 5 ảnh chạy thử
```

## Đặc tả

| Endpoint | Scope | Status code | Ghi chú |
|---|---|---|---|
| `POST /auth/login` | không (public) | 200, 400, 401, 403, 429, 500 | 401 chung cho mọi sai thông tin; 403 chỉ trả khi mật khẩu đã đúng; `Cache-Control: no-store` |
| `POST /auth/refresh` | không (dùng `refresh_token` trong body) | 200, 400, 401, 429, 500 | Refresh token dùng một lần; dùng lại token cũ thì thu hồi cả phiên |
| `GET /posts/{id}` | `posts:read` | 200, 400, 401, 403, 404, 429, 500 | `id` là UUID; bài không tồn tại và bài không được xem đều trả 404 |

Xác thực: OAuth2 (password flow), access token dạng Bearer JWT, sống 900 giây. Mọi lỗi có dạng `{"code", "message", "request_id"}`; `429` kèm header `Retry-After`; `401` kèm `WWW-Authenticate`. Đặc tả đã kiểm tra hợp lệ bằng `openapi-spec-validator`.

## Chạy thử

```powershell
npm install -g @stoplight/prism-cli
prism mock socialNetwork.yaml -p 4010      # mock server: http://127.0.0.1:4010
```

Swagger UI (`index.html` trỏ tới `./socialNetwork.yaml`) mở bằng Live Server tại `http://127.0.0.1:5500/index.html`. Để Swagger UI gọi vào mock, thêm vào mục `servers:` của yaml:

```yaml
  - url: http://127.0.0.1:4010
    description: Mock server local (chạy bằng Prism)
```

Muốn mock trả mã lỗi khác, thêm header `Prefer: code=404` (hoặc mã khác đã khai báo trong spec).

---

## Ảnh chạy thử

**1. Swagger UI nạp `socialNetwork.yaml`: 3 endpoint, bảng scope / status code, server là mock Prism `127.0.0.1:4010`**

![Swagger UI](test/Screenshot%202026-10-26%20221632.png)

**2. `POST /auth/login` → `200`, body đúng schema `TokenResponse`, header `cache-control: no-store`**

![POST /auth/login](test/Screenshot%202026-10-26%20222328.png)

**3. `POST /auth/refresh` → `200`, body đúng schema `TokenResponse`, header `cache-control: no-store`**

![POST /auth/refresh](test/Screenshot%202026-10-26%20222347.png)

**4. `GET /posts/{id}` với `id = 01` → Swagger UI chặn ngay: "Value must be a Guid" (do `format: uuid`)**

![id không phải UUID](test/Screenshot%202026-10-26%20222418.png)

**5. `GET /posts/{uuid}` không kèm token → `401 Unauthorized`, body `UNAUTHORIZED`, header `www-authenticate: Bearer error="invalid_token"`**

![GET /posts/id không có token](test/Screenshot%202026-10-26%20222636.png)

---

## Rà soát bảo mật

`SecurityAudit.md` liệt kê 9 điểm: dò email qua thông báo lỗi, brute-force, đánh cắp / replay refresh token, lộ token qua log và cache, IDOR/BOLA, lộ sự tồn tại của bài riêng tư, trả dữ liệu thừa, lộ chi tiết nội bộ qua lỗi 500, xác thực JWT lỏng. Đặc tả đã phản ánh các biện pháp chính: 401 chung, refresh một lần, `no-store`, 404 chung, schema `Post` chỉ gồm trường cần thiết, `request_id` thay cho stack trace.

## Ghi chú

- Các giá trị `"string"`, `900` trong ảnh 2 và 3 là dữ liệu mẫu do Prism sinh từ schema, không phải server thật.
- Ảnh 4 là kiểm tra phía Swagger UI (request không được gửi đi). Gọi thẳng vào mock với id sai thì nhận `400 BAD_REQUEST`.
- `app.py` đang trống và file yaml trong zip chưa có mục server `127.0.0.1:4010` (ảnh 1 có), xem phần "Chạy thử".
