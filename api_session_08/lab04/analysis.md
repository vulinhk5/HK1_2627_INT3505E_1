# Lab 4 - Phân tích load test Books API với Locust
## 0. Cách đo
| | |
|---|---|
| Đối tượng test | `app.py` của Lab 3 (Flask, dữ liệu in-memory), chạy bằng `python -m app --port 5000` |
| Máy đo | Windows; **Locust và API chạy chung một máy** (tranh nhau CPU); host `http://127.0.0.1:5000` |
| Locustfile | 4 task: `GET /books` (4), `GET /books/[id]` (3), `search_by_year` (2, 1% lỗi giả lập 500), `POST /books` (1); think time 0.5–1.5 s |
| Kịch bản | A: `-u 10 -r 2 -t 30s` · B: `-u 50 -r 5 -t 60s` · C: `-u 200 -r 50 -t 30s` |
| Lưu ý | App lưu sách trong RAM và POST làm danh sách phình ra, nên **khởi động lại app trước mỗi kịch bản** để A/B/C bắt đầu cùng một trạng thái |

Toàn bộ số liệu dưới đây lấy từ `reports/A.html`, `B.html`, `C.html`.

| Kịch bản | User | Requests | RPS | p50 | **p95** | p99 | max | Fail |
|---|---|---|---|---|---|---|---|---|
| A — baseline | 10 | 277 | 9.6 | 6 ms | **38 ms** | 150 ms | 189 ms | 0 (0%) |
| B — load test | 50 | 2718 | 46.0 | 7 ms | **23 ms** | 65 ms | 150 ms | 7 (0.26%) |
| C — spike | 200 | 5484 | 185.2 | 14 ms | **87 ms** | 130 ms | 258 ms | 8 (0.15%) |

p95 (ms) và fail rate theo endpoint:

| Endpoint | A (10 user) | B (50 user) | C (200 user) |
|---|---|---|---|
| `GET /books` | 27 / 0% | 23 / 0% | 85 / 0% |
| `GET /books/[id]` | 56 / 0% | 22 / 0% | 91 / 0% |
| `GET /books?year=[year]` | 45 / 0% (0/52) | 22 / 1.26% (7/555) | 88 / 0.74% (8/1082) |
| `POST /books` | 51 / 0% | 26 / 0% | 85 / 0% |

---
## 1. Kịch bản nào có p95 cao nhất? Vì sao?

Kịch bản C (spike, 200 user): p95 = 87 ms, cao hơn B (23 ms) 3.8 lần trong khi số user chỉ gấp 4 lần. Cả p50 cũng tăng gấp đôi (7 → 14 ms) và p99 tăng từ 65 lên 130 ms, nên đây là sự chậm đi trên toàn bộ phân phối, không phải vài request lẻ.

(p95 của A là 38 ms, cao hơn B, nhưng không có nghĩa tải nhẹ thì chậm hơn: A chỉ có 277 request nên p95 chỉ dựa trên khoảng 14 request chậm nhất. Biểu đồ *Response Times* của `A.html` cho thấy p95 phần lớn thời gian chỉ ~10 ms và có một đợt ngắn ~90 ms, đủ kéo p95 tổng lên. Với mẫu nhỏ như vậy, p95 của A không đáng tin để so sánh.)

Nguyên nhân của C, theo mức độ có bằng chứng:
- Tải đồng thời cao nhất, và mọi endpoint chậm như nhau. Ở C, p95 của 4 endpoint đều ở 85–91 ms, dù `GET /books/[id]` (tra dict) nhẹ hơn nhiều so với `GET /books` (trả cả danh sách). Điều này cho thấy nút thắt nằm ở tầng chung (tiến trình/CPU), không phải ở một endpoint cụ thể.
- Không chỉ do giai đoạn ramp-up. Trên biểu đồ *Response Times* của `C.html`, p95 ở mốc đầu (đang spawn 200 user) là ~130 ms, rồi ổn định ở ~68–85 ms đến hết kịch bản. Vậy riêng đợt spawn làm đuôi chậm thêm, nhưng ngay cả khi đã đủ 200 user thì p95 vẫn cao hơn nhiều so với B (12–47 ms theo từng mốc).
- Một tiến trình Python + GIL, chạy chung máy với Locust. Flask dev server (`app.run`) xử lý mỗi kết nối bằng một thread nhưng phần code Python (`jsonify`, tra dict) vẫn bị tuần tự hóa qua GIL, và Locust cũng ăn CPU của cùng máy. Càng nhiều user đồng thời thì thời gian chờ CPU càng dài.
- Dữ liệu phình ra.** `GET /books` trả cả `BOOKS` và POST không bao giờ xóa: cuối kịch bản có khoảng 27 / 257 / 573 sách (A/B/C). Nhưng ở C `GET /books/[id]` (chi phí O(1)) có p95 = 91 ms, không thấp hơn `GET /books` (85 ms), nên kích thước payload không phải nguyên nhân chính.

RPS tăng gần tuyến tính theo user (0.96 / 0.92 / 0.93 RPS mỗi user), nghĩa là app chưa bão hòa ở 200 user: thông lượng vẫn theo kịp, chỉ có độ trễ tăng lên.
## 2. Endpoint nào có fail rate tăng theo số user?
Không có endpoint nào. Server không trả về mã 4xx/5xx nào trong cả ba kịch bản. Cột fail% duy nhất khác 0 là `GET /books?year=...`, và 100% lỗi đó là `Simulated 500 Internal Server Error (1% fail rate)` do `locustfile.py` chủ động đánh dấu ở Bước 1, không phải lỗi của server.

Vì sao nhìn như thay đổi theo user nhưng không phải: fail% của search là 0% (0/52) → 1.26% (7/555) → 0.74% (8/1082). Với tỉ lệ cài đặt 1%, số lỗi kỳ vọng ở ba kịch bản là 0.5 / 5.5 / 10.8 (độ lệch chuẩn khoảng 0.7 / 2.3 / 3.3). Số lỗi quan sát được là 0 / 7 / 8, đều nằm trong khoảng ±1 độ lệch chuẩn so với kỳ vọng, nên đó chỉ là dao động ngẫu nhiên của mẫu nhỏ, không phải xu hướng theo tải. Ở A chỉ có 52 request search nên hầu như chắc chắn thấy 0 lỗi.

Đoán dựa trên code: nếu cứ tăng user thì chỗ nào sẽ hỏng trước?
- `GET /books` (và `/books?year=` vì `year` bị bỏ qua): `list(BOOKS.values())` rồi `jsonify` toàn bộ dict, không phân trang, dữ liệu chỉ tăng. Chi phí mỗi request là O(n) và n lớn dần theo thời gian chạy và theo tỉ lệ POST. Đây là endpoint sẽ chậm trước và chạm timeout của client trước.
- `POST /books`: `_next_id` là biến global, thao tác "đọc → ghi `BOOKS[_next_id]` → tăng" không có lock. Với Flask chạy nhiều thread, hai POST đồng thời về lý thuyết có thể nhận cùng id và ghi đè nhau (mất dữ liệu mà không có lỗi HTTP, nên Locust không phát hiện được). Đây là rủi ro tiềm ẩn, cần lock hoặc id do DB cấp.
- Flask dev server: một tiến trình, không dùng cho production. Cần chuyển sang gunicorn/uvicorn nhiều worker.

## 3. SLO p95 < 300 ms: kịch bản nào đạt? Baseline cho CI gate
Cả ba kịch bản đều đạt: p95 = 38 / 23 / 87 ms. Dư địa nhỏ nhất ở C: 300 / 87 ≈ 3.4 lần, và max ở C là 258 ms (sát ngưỡng 300 ms dù SLO chỉ xét p95). Đây là app in-memory chạy local, chưa có DB hay mạng, nên trên staging/prod con số sẽ cao hơn: ở thí nghiệm bonus, chỉ cần thêm 50 ms độ trễ DB thì pool = 20 đã có p95 = 240 ms (sát SLO) còn pool = 5 thì vỡ SLO hoàn toàn (p95 = 1900 ms).

**Đề xuất baseline cho CI gate:**

| Mục | Đề xuất | Lý do |
|---|---|---|
| Profile chạy trong CI | **Kịch bản B** (`-u 50 -r 5 -t 60s`), chạy ở mỗi PR/merge | Tải đại diện, đủ nhiều request (2718) để p95 ổn định hơn A, chỉ 1 phút |
| Kịch bản C | Chạy hằng đêm, chỉ để quan sát, **không chặn build** | p95 theo từng mốc dao động mạnh (68–130 ms), dễ gây flaky |
| Baseline đo được (B) | p95 = **23 ms**, p99 = 65 ms, fail = 0.26% | Từ `reports/B.html` |
| Ngưỡng p95 | **< 100 ms** (≈ 4 × baseline) | p95 theo từng mốc ở B đã dao động 12–47 ms nên ngưỡng 50 ms sẽ flaky; 100 ms ≈ mức p95 của kịch bản spike hiện tại (87 ms): nếu tải thường mà p95 đã bằng spike thì là hồi quy thật; vẫn thấp hơn SLO 3 lần |
| Ngưỡng fail | **≤ 1%** | 1% lỗi giả lập × ~20% lượng request search ⇒ mức "bình thường" ≈ 0.2–0.3%; vượt 1% nghĩa là có lỗi thật |
| SLO 300 ms | Giữ làm ngưỡng cảnh báo trên prod | Trần tuyệt đối theo yêu cầu |

Lệnh gate (đã có trong `locustfile.py`, thoát mã 0 nếu đạt, mã 1 nếu vi phạm):

```bash
CI_GATE=1 SLO_P95_MS=100 SLO_MAX_FAIL_RATIO=0.01 \
  locust -f locustfile.py --host http://127.0.0.1:5000 --headless -u 50 -r 5 -t 60s --html reports/ci.html
```

## Bonus: connection pool giới hạn 5, 200 user đồng thời thì sao?
`app.py` hiện không có DB hay pool, nên mô phỏng bằng cách bọc **nguyên `app.py`** (không sửa) với một semaphore N chỗ và 50 ms độ trễ "truy vấn DB" trong lúc giữ connection (`pool_whatif.py`; quá 2 s chờ thì trả 503, giống `pool_timeout`). 
- Chỉ 5 request được truy vấn DB cùng lúc. Request thứ 6 trở đi **bị chặn chờ connection** (thread chỉ ngồi chờ, gần như không tốn CPU).
- Thông lượng bị chặn ở trần `pool / thời gian giữ connection` (định luật Little): 5 / 0.05 s ≈ **100 RPS**. 200 user (think time ~1 s) muốn ~190 RPS nên vượt trần, hàng đợi dài ra và request nào cũng phải chờ: thời gian phản hồi ≈ N/X − think ≈ 200/92 − 1 ≈ **1.2 s**, cùng cỡ với thời gian phản hồi đo được (trung bình 1.0 s, p50 1.1 s).
- Ai chờ quá `pool_timeout` thì nhận lỗi (503 ở thí nghiệm; ở SQLAlchemy là `QueuePool limit of size 5 ... reached`).
- Dấu hiệu nhận biết: **latency cao nhưng CPU thấp**, p50 gần p95 (mọi người cùng xếp hàng), RPS đi ngang dù tăng user.

| Cấu hình (DB 50 ms, 200 user) | RPS | p50 | p95 | p99 | Fail |
|---|---|---|---|---|---|
| pool = 5 | **92.4** | **1100 ms** | **1900 ms** | 2100 ms | 42 / 2779 (1.51%): 32 lỗi 503 + 10 lỗi giả lập |
| pool = 20 | 167.0 | 82 ms | 240 ms | 430 ms | 12 / 4892 (0.25%): toàn bộ là lỗi giả lập |

## Cách chạy lại

```bash
pip install flask locust
locust -f locustfile.py --host http://127.0.0.1:5000 --headless -u 10  -r 2  -t 30s --html reports/A.html
locust -f locustfile.py --host http://127.0.0.1:5000 --headless -u 50  -r 5  -t 60s --html reports/B.html
locust -f locustfile.py --host http://127.0.0.1:5000 --headless -u 200 -r 50 -t 30s --html reports/C.html
```

