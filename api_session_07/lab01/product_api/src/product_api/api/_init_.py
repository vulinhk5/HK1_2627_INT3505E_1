from .products import products_bp


def register_blueprints(app):
    app.register_blueprint(products_bp)