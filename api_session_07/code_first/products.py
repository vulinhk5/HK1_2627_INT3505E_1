from flask.views import MethodView
from flask_smorest import Blueprint, abort

from models import Product, db
from schemas import ProductInSchema, ProductSchema

blp = Blueprint(
    "products",
    __name__,
    url_prefix="/products",
    description="Manage products",
)

class ProductList(MethodView):
    @blp.arguments(ProductInSchema) 
    @blp.response(201, ProductSchema)
    def post(self, data):
        """Tạo sản phẩm mới"""
        p = Product(**data)
        db.session.add(p)
        db.session.commit()
        return p

    @blp.response(200, ProductSchema(many=True))
    def get(self):
        """Liệt kê toàn bộ sản phẩm"""
        return db.session.execute(
            db.select(Product).order_by(Product.id)
        ).scalars().all()


class ProductItem(MethodView):
    @blp.response(200, ProductSchema)
    @blp.alt_response(404, description="Not Found")
    def get(self, product_id):
        """Lấy một sản phẩm theo id"""
        p = db.session.get(Product, product_id)
        if p is None:
            abort(404, message=f"Product {product_id} not found")
        return p

blp.add_url_rule("", "product_list", view_func=ProductList)
blp.add_url_rule("/<int:product_id>", "product_item", view_func=ProductItem)
