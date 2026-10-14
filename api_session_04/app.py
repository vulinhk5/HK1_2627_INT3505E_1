import os
import re
import uuid
from datetime import datetime, timezone
from threading import Lock

from flask import Flask, Response, jsonify, request

API_PREFIX = "/v1"
STATUSES = ("todo", "in_progress", "done")
PRIORITIES = ("low", "medium", "high")
TITLE_MAX_LENGTH = 200
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

JWT_SECRET = os.environ.get("JWT_SECRET")
if JWT_SECRET:
    import jwt 

app = Flask(__name__)
app.json.sort_keys = False  
app.json.ensure_ascii = False 


_tasks = {}
_lock = Lock()

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def error_response(status_code, code, message, details=None):
    body = {"code": code, "message": message}
    if details:
        body["details"] = details
    return jsonify(body), status_code


def validation_error(details):
    return error_response(422, "VALIDATION_ERROR", "Request body is invalid", details)


def not_found():
    return error_response(404, "NOT_FOUND", "Không tìm thấy task")


def is_valid_date(value):
    if not isinstance(value, str) or not DATE_PATTERN.match(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def is_valid_uuid(value):
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value.lower()
    except ValueError:
        return False


def validate_task_fields(data, partial):
    clean = {}
    details = []

    def add_error(field, issue):
        details.append({"field": field, "issue": issue})

    if "title" in data:
        title = data["title"]
        if not isinstance(title, str):
            add_error("title", "must be a string")
        elif len(title) < 1:
            add_error("title", "must not be empty")
        elif len(title) > TITLE_MAX_LENGTH:
            add_error("title", f"must be at most {TITLE_MAX_LENGTH} characters")
        else:
            clean["title"] = title
    elif not partial:
        add_error("title", "is required")

    for field, allowed in (("status", STATUSES), ("priority", PRIORITIES)):
        if field in data:
            if isinstance(data[field], str) and data[field] in allowed:
                clean[field] = data[field]
            else:
                add_error(field, "must be one of: " + ", ".join(allowed))

    if "dueDate" in data:
        if data["dueDate"] is None or is_valid_date(data["dueDate"]):
            clean["dueDate"] = data["dueDate"]
        else:
            add_error("dueDate", "must be a date in YYYY-MM-DD format or null")

    if "assigneeId" in data:
        if data["assigneeId"] is None or is_valid_uuid(data["assigneeId"]):
            clean["assigneeId"] = data["assigneeId"]
        else:
            add_error("assigneeId", "must be a UUID or null")

    return clean, details


def get_json_object():
    data = request.get_json(force=True, silent=True)
    return data if isinstance(data, dict) else None

@app.before_request
def require_bearer_token():
    if not request.path.startswith(API_PREFIX + "/"):
        return None

    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        return error_response(401, "UNAUTHORIZED", "Thiếu hoặc sai Bearer token")

    if JWT_SECRET:
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return error_response(401, "UNAUTHORIZED", "Thiếu hoặc sai Bearer token")
    return None


@app.get(f"{API_PREFIX}/tasks")
def list_tasks():
    """listTasks - GET /tasks?status=..."""
    status = request.args.get("status")
    if status is not None and status not in STATUSES:
        return validation_error(
            [{"field": "status", "issue": "must be one of: " + ", ".join(STATUSES)}]
        )

    with _lock:
        items = [dict(t) for t in _tasks.values() if status is None or t["status"] == status]
    return jsonify(items), 200


@app.post(f"{API_PREFIX}/tasks")
def create_task():
    """createTask - POST /tasks"""
    data = get_json_object()
    if data is None:
        return validation_error([{"field": "body", "issue": "must be a JSON object"}])

    clean, details = validate_task_fields(data, partial=False)
    if details:
        return validation_error(details)

    now = now_iso()
    task = {
        "id": str(uuid.uuid4()),
        "title": clean["title"],
        "status": clean.get("status", "todo"),
        "priority": clean.get("priority", "medium"),
        "dueDate": clean.get("dueDate"),
        "assigneeId": clean.get("assigneeId"),
        "createdAt": now,
        "updatedAt": now,
    }
    with _lock:
        _tasks[task["id"]] = task

    response = jsonify(task)
    response.status_code = 201
    response.headers["Location"] = f"{API_PREFIX}/tasks/{task['id']}"
    return response


@app.get(f"{API_PREFIX}/tasks/<task_id>")
def get_task_by_id(task_id):
    """getTaskById - GET /tasks/{taskId}"""
    with _lock:
        task = _tasks.get(task_id)
        result = dict(task) if task else None
    if result is None:
        return not_found()
    return jsonify(result), 200


@app.patch(f"{API_PREFIX}/tasks/<task_id>")
def patch_task(task_id):
    """patchTask - PATCH /tasks/{taskId}: chỉ cập nhật các field được gửi lên."""
    with _lock:
        exists = task_id in _tasks
    if not exists:
        return not_found()

    data = get_json_object()
    if data is None:
        return validation_error([{"field": "body", "issue": "must be a JSON object"}])

    clean, details = validate_task_fields(data, partial=True)
    if details:
        return validation_error(details)
    if not clean:
        return validation_error(
            [{"field": "body", "issue": "must contain at least one of: "
              "title, status, priority, dueDate, assigneeId"}]
        )

    with _lock:
        task = _tasks.get(task_id)
        if task is None:  
            return not_found()
        task.update(clean)
        task["updatedAt"] = now_iso()
        result = dict(task)
    return jsonify(result), 200


@app.delete(f"{API_PREFIX}/tasks/<task_id>")
def delete_task(task_id):
    with _lock:
        removed = _tasks.pop(task_id, None)
    if removed is None:
        return not_found()
    return Response(status=204)

@app.errorhandler(404)
def handle_404(_error):
    return error_response(404, "NOT_FOUND", "Không tìm thấy tài nguyên")


@app.errorhandler(405)
def handle_405(_error):
    return error_response(405, "METHOD_NOT_ALLOWED", "Phương thức không được hỗ trợ")


@app.errorhandler(500)
def handle_500(_error):
    return error_response(500, "INTERNAL_ERROR", "Lỗi hệ thống")


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )