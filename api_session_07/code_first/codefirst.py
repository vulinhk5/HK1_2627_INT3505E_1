import os


from flask import Flask
from flask_smorest import Api

from models import db
from products import blp as products_blp

app = Flask(__name__)
app.config.update(
    API_TITLE="Product API",
    API_VERSION="1.0.0",
    OPENAPI_VERSION="3.0.3",
    API_SPEC_OPTIONS={
        "info": {"description": "Code-First: spec được sinh tự động từ resource."},
        "servers": [{"url": "/"}],
    },

    OPENAPI_URL_PREFIX="/",             
    OPENAPI_JSON_PATH="openapi.json",   
    OPENAPI_SWAGGER_UI_PATH="/ui",     
    OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///products.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

db.init_app(app)

api = Api(app)
api.register_blueprint(products_blp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)
