Kết quả kiểm thử API Bookstore

Dưới đây là các ảnh chụp màn hình minh họa kết quả chạy và kiểm thử các API của dự án Bookstore bằng lệnh curl.

1. Thêm mới sách (POST /api/v1/books)

Thực hiện gửi request POST để tạo mới sách và nhận về HTTP Status 201 CREATED.

2. Lấy danh sách tất cả sách (GET /api/v1/books)

Lấy toàn bộ dữ liệu sách hiện có trong database.

3. Lấy thông tin chi tiết một cuốn sách (GET /api/v1/books/)

Lấy thông tin của một cuốn sách cụ thể bằng ID.

Trường hợp thành công (HTTP 200 OK):


Trường hợp sách không tồn tại (HTTP 404 NOT FOUND):


4. Bắt lỗi Validate dữ liệu đầu vào (POST /api/v1/books)

Kiểm tra trường hợp gửi thiếu thuộc tính bắt buộc (ví dụ: title) hoặc sai định dạng. Trả về HTTP Status 422 UNPROCESSABLE ENTITY.

5. Log hoạt động của Flask Server

Ghi nhận toàn bộ các request (POST, GET) và status code tương ứng trả về từ server.