from flask import Blueprint, jsonify, url_for
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from .errors import Conflict, NotFound, OutOfStock
from ..extensions import db
from ..models import Product
from .schemas.products import (
    PRODUCT_OUT,
    PRODUCT_OUT_MANY,
    ProductIn,
    ProductPatch,
    ReserveIn,
)
from .utils import json_body, parse_pagination

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


def _get_active_or_404(product_id: int) -> Product:
    product = db.session.get(Product, product_id)
    if product is None or product.archived:
        raise NotFound(message=f"product {product_id} not found")
    return product


@products_bp.get("")
def list_products():
    page, size = parse_pagination()
    active = Product.archived.is_(False)
    rows = (
        db.session.execute(
            select(Product)
            .where(active)
            .order_by(Product.id)
            .offset((page - 1) * size)
            .limit(size)
        )
        .scalars()
        .all()
    )
    total = db.session.scalar(select(func.count()).select_from(Product).where(active))
    return jsonify(
        {"items": PRODUCT_OUT_MANY.dump(rows), "page": page, "size": size, "total": total}
    )


@products_bp.get("/<int:product_id>")
def get_product(product_id):
    return jsonify(PRODUCT_OUT.dump(_get_active_or_404(product_id)))


@products_bp.post("")
def create_product():
    body = ProductIn().load(json_body()) 
    product = Product(**body)
    db.session.add(product)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict(message="sku already exists") from None
    response = jsonify(PRODUCT_OUT.dump(product))
    response.status_code = 201
    response.headers["Location"] = url_for("products.get_product", product_id=product.id)
    return response


@products_bp.post("/<int:product_id>/reserve")
def reserve_product(product_id):
    body = ReserveIn().load(json_body())
    qty = body["qty"]
    product = _get_active_or_404(product_id)
    available = product.qty_in_stock


    result = db.session.execute(
        update(Product)
        .where(Product.id == product_id, Product.qty_in_stock >= qty)
        .values(qty_in_stock=Product.qty_in_stock - qty)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.session.rollback()
        raise OutOfStock(message=f"only {available} left")
    db.session.commit()
    return jsonify(PRODUCT_OUT.dump(product))  

@products_bp.patch("/<int:product_id>")
def patch_product(product_id):
    body = ProductPatch().load(json_body())
    product = _get_active_or_404(product_id)
    for key, value in body.items():
        setattr(product, key, value)
    db.session.commit()
    return jsonify(PRODUCT_OUT.dump(product))


@products_bp.delete("/<int:product_id>")
def delete_product(product_id):
    product = _get_active_or_404(product_id)
    product.archived = True
    db.session.commit()
    return "", 204
