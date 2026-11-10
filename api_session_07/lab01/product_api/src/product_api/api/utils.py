from flask import request

from .errors import BadRequest, Unprocessable

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


def json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BadRequest(message="Request body must be a valid JSON object")
    return data


def parse_pagination() -> tuple[int, int]:
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_PAGE_SIZE))
    except ValueError:
        raise Unprocessable(message="page and size must be integers") from None
    return max(1, page), min(MAX_PAGE_SIZE, max(1, size))
