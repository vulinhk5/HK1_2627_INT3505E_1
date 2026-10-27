Phạm vi: `POST /auth/login`, `POST /auth/refresh`, `GET /posts/{id}`

## Các điểm có thể bị lộ

| # | Điểm có thể lộ | Endpoint | Rủi ro | Cách giảm thiểu |
|---|----------------|----------|--------|------------------------------------------|
| 1 | **User enumeration**: thông báo lỗi hoặc thời gian phản hồi khác nhau giữa "email không tồn tại" và "sai mật khẩu"; 403 "tài khoản bị khóa" trả trước khi kiểm tra mật khẩu | `/auth/login` | Kẻ tấn công dò được email nào có tài khoản | Sai thông tin luôn là 401 với một thông báo chung; chỉ trả 403 sau khi mật khẩu đúng; so sánh hash với thời gian hằng định |
| 2 | **Brute-force / credential stuffing** | `/auth/login` | Đoán mật khẩu hàng loạt bằng danh sách mật khẩu bị lộ | Rate limit theo IP và theo tài khoản (429 + `Retry-After`), khóa tạm sau nhiều lần sai, CAPTCHA, phát hiện đăng nhập bất thường |
| 3 | **Refresh token bị đánh cắp hoặc replay** | `/auth/refresh` | Kẻ trộm token duy trì phiên vô thời hạn | Rotation (dùng 1 lần), phát hiện dùng lại token cũ thì thu hồi toàn bộ phiên, lưu hash của token trong DB, TTL ngắn, cho phép đăng xuất để thu hồi |
| 4 | **Token lộ qua log, cache, URL hoặc kênh không mã hóa** | `/auth/login`, `/auth/refresh` | Token nằm trong log, proxy cache hoặc trình duyệt | Chỉ HTTPS + HSTS, token chỉ nằm trong body (không đưa lên URL), `Cache-Control: no-store`, không log body request/response của auth |
| 5 | **IDOR / BOLA**: chỉ kiểm tra scope mà không kiểm tra quyền xem từng bài | `/posts/{id}` | Có scope `posts:read` là đọc được bài riêng tư của người khác | Kiểm tra visibility và quan hệ bạn bè ở server cho mỗi request; dùng UUID thay vì id tăng dần để khó đoán |
| 6 | **Lộ sự tồn tại của bài viết**: 403 cho bài riêng tư, 404 cho bài không có | `/posts/{id}` | Dò được id nào là bài riêng tư | Bài không tồn tại và bài không được xem đều trả 404 (đã ghi trong spec); 403 chỉ dùng cho thiếu scope |
| 7 | **Lộ dữ liệu thừa (excessive data exposure)** | `/posts/{id}` | Response trả luôn email tác giả, IP, cờ nội bộ do serialize thẳng model DB | Dùng DTO whitelist: schema `Post` chỉ gồm `id`, `author{id, display_name}`, `content`, `visibility`, `created_at` |
| 8 | **Lộ thông tin nội bộ qua lỗi 500** | cả 3 endpoint | Stack trace, câu SQL, tên bảng giúp kẻ tấn công hiểu hệ thống | Thông báo chung kèm `request_id`, chi tiết chỉ ghi log phía server |
| 9 | **JWT xác thực lỏng**: chấp nhận `alg: none`, không kiểm tra `exp`, `aud`, `scope` | `/posts/{id}` | Giả mạo token hoặc dùng token cho dịch vụ khác | Cố định thuật toán ký, kiểm tra chữ ký, `exp`, `aud`, `iss` và scope; access token sống ngắn (~15 phút) |
