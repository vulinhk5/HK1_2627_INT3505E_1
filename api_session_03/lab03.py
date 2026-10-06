import base64
import json

from flask import Flask, jsonify, request

app = Flask(__name__)

ORDERS = [
    {"id": 1,  "customer_id": 1, "status": "paid",      "total": 50,  "created_at": "2026-01-01"},
    {"id": 2,  "customer_id": 2, "status": "pending",   "total": 30,  "created_at": "2026-01-02"},
    {"id": 3,  "customer_id": 1, "status": "paid",      "total": 80,  "created_at": "2026-01-03"},
    {"id": 4,  "customer_id": 3, "status": "shipped",   "total": 30,  "created_at": "2026-01-04"},
    {"id": 5,  "customer_id": 2, "status": "paid",      "total": 120, "created_at": "2026-01-05"},
    {"id": 6,  "customer_id": 3, "status": "cancelled", "total": 50,  "created_at": "2026-01-06"},
    {"id": 7,  "customer_id": 1, "status": "shipped",   "total": 80,  "created_at": "2026-01-07"},
    {"id": 8,  "customer_id": 2, "status": "paid",      "total": 30,  "created_at": "2026-01-08"},
    {"id": 9,  "customer_id": 3, "status": "pending",   "total": 100, "created_at": "2026-01-09"},
    {"id": 10, "customer_id": 1, "status": "paid",      "total": 50,  "created_at": "2026-01-10"},
    {"id": 11, "customer_id": 2, "status": "shipped",   "total": 70,  "created_at": "2026-01-11"},
    {"id": 12, "customer_id": 3, "status": "paid",      "total": 100, "created_at": "2026-01-12"},
]

ALL_FIELDS = ["id", "customer_id", "status", "total", "created_at"]
SORTABLE = ["id", "total", "created_at"]


def bad_request(message):
    return jsonify({"error": message}), 400

def encode_cursor(sort, value, last_id):
    raw = json.dumps({"sort": sort, "v": value, "id": last_id})
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor, sort, field):
    """Trả về (value, id). Nếu cursor hỏng thì trả về None."""
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        if data["sort"] != sort:
            return None
        if type(data["v"]) is not type(ORDERS[0][field]):
            return None
        if type(data["id"]) is not int:
            return None
        return data["v"], data["id"]
    except Exception:
        return None

@app.get("/orders")
def list_orders():
    args = request.args

    try:
        limit = int(args.get("limit", 10))
    except ValueError:
        return bad_request("limit phải là số nguyên")
    if not 1 <= limit <= 100:
        return bad_request("limit phải từ 1 đến 100")
    
    items = ORDERS

    if "status" in args:
        items = [o for o in items if o["status"] == args["status"]]

    if "customer_id" in args:
        try:
            customer_id = int(args["customer_id"])
        except ValueError:
            return bad_request("customer_id phải là số nguyên")
        items = [o for o in items if o["customer_id"] == customer_id]

    sort = args.get("sort", "id")
    desc = sort.startswith("-")
    field = sort.lstrip("-")
    if field not in SORTABLE:
        return bad_request(f"sort chỉ nhận: {', '.join(SORTABLE)} (thêm - để giảm dần)")
    items = sorted(items, key=lambda o: (o[field], o["id"]), reverse=desc)

    cursor = args.get("cursor")
    if cursor:
        last = decode_cursor(cursor, sort, field)
        if last is None:
            return bad_request("cursor không hợp lệ")
        if desc:
            items = [o for o in items if (o[field], o["id"]) < last]
        else:
            items = [o for o in items if (o[field], o["id"]) > last]

    page = items[:limit]
    has_more = len(items) > limit

    next_cursor = None
    if has_more:
        last_item = page[-1]
        next_cursor = encode_cursor(sort, last_item[field], last_item["id"])

    if "fields" in args:
        wanted = args["fields"].split(",")
        unknown = [f for f in wanted if f not in ALL_FIELDS]
        if unknown:
            return bad_request(f"field không tồn tại: {', '.join(unknown)}")
        page = [{f: o[f] for f in wanted} for o in page]

    return jsonify({"data": page, "next_cursor": next_cursor})

if __name__ == "__main__":
    app.run(port=5000, debug=True)