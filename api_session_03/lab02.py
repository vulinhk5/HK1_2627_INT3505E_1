import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
logger = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"

class ProblemError(Exception):
    def __init__(self, status, title, detail, type_="about:blank"):
        super().__init__(detail)
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type_

def problem_response(status, title, detail, type_="about:blank"):
    body = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.path, 
    }
    response = jsonify(body)
    response.status_code = status         
    response.content_type = PROBLEM_JSON 
    return response

@app.errorhandler(ProblemError)
def handle_problem_error(e):
    return problem_response(e.status, e.title, e.detail, e.type)

@app.errorhandler(HTTPException) 
def handle_http_exception(e):
    return problem_response(e.code, e.name, e.description)

@app.errorhandler(Exception)  
def handle_unexpected_error(e):
    logger.exception("Unhandled error at %s %s", request.method, request.path)
    return problem_response(
        500, "Internal Server Error", "An unexpected error occurred, please try again later."
    )

RESOURCES = {
    1: {"id": 1, "name": "Into the magic shop"},
    2: {"id": 2, "name": "The ones who walk away from omelas"},
    3: {"id": 3, "name": "A little life"},
    4: {"id": 4, "name": "Demian"},
}

@app.get("/resources/<int:resource_id>")
def get_resource(resource_id):
    resource = RESOURCES.get(resource_id)
    if resource is None:
        raise ProblemError(
            status=404,
            title="Resource Not Found",
            detail=f"Cannot find resource with id = {resource_id}",
            type_="https://example.com/problems/resource-not-found",
        )
    return jsonify(resource)


@app.get("/boom")  
def boom():
    raise RuntimeError("password = 1234567") 


if __name__ == "__main__":
    app.run(debug=False)