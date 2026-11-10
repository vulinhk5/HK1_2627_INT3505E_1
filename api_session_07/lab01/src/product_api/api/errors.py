from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException, MethodNotAllowed


class ApiError(Exception):

    status_code = 500
    code = "internal_error"

    def __init__(self, message="", *, code=None, status=None, errors=None):
        super().__init__(message)
        if code:
            self.code = code
        if status:
            self.status_code = status
        self.message = message or self.code.replace("_", " ")
        self.errors = errors


class BadRequest(ApiError):
    status_code = 400
    code = "bad_request"


class NotFound(ApiError):
    status_code = 404
    code = "not_found"


class Conflict(ApiError):
    status_code = 409
    code = "conflict"


class OutOfStock(Conflict):
    code = "out_of_stock"


class Unprocessable(ApiError):
    status_code = 422
    code = "validation_error"


def error_response(status, code, message, errors=None):
    body = {"error": code, "detail": message, "code": code, "message": message}
    if errors:
        body["errors"] = errors
    response = jsonify(body)
    response.status_code = status
    return response


def _flatten(errors, path=""):
    """{'items': {'0': {'qty': ['msg']}}} -> ['items.0.qty: msg']"""
    if isinstance(errors, dict):
        out = []
        for key, value in errors.items():
            out += _flatten(value, f"{path}.{key}" if path else str(key))
        return out
    if isinstance(errors, (list, tuple)):
        out = []
        for item in errors:
            out += _flatten(item, path)
        return out
    return [f"{path}: {errors}" if path else str(errors)]


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def _on_api_error(err):
        return error_response(err.status_code, err.code, err.message, err.errors)

    @app.errorhandler(ValidationError)
    def _on_validation_error(err):
        messages = err.normalized_messages()
        detail = "; ".join(_flatten(messages)) or "Validation failed"
        return error_response(422, "validation_error", detail, messages)

    @app.errorhandler(HTTPException)
    def _on_http_error(err):
        code = (err.name or "error").lower().replace(" ", "_")
        response = error_response(err.code or 500, code, err.description or err.name)
        if isinstance(err, MethodNotAllowed) and err.valid_methods:
            response.headers["Allow"] = ", ".join(err.valid_methods)
        return response

    @app.errorhandler(Exception)
    def _on_unhandled(err):
        app.logger.exception("unhandled_exception")
        return error_response(500, "internal_error", "Unexpected server error")
