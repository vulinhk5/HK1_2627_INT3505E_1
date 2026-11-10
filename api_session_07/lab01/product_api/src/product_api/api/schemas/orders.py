from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from .common import INT_MAX, not_blank, strict_int
from .products import ProductBrief


class OrderItemIn(Schema):
    product_id = strict_int(required=True, validate=validate.Range(min=1, max=INT_MAX))
    qty = strict_int(required=True, validate=validate.Range(min=1, max=INT_MAX))


class OrderIn(Schema):

    customer_name = fields.Str(
        required=True, validate=[validate.Length(min=1, max=255), not_blank]
    )
    items = fields.List(
        fields.Nested(OrderItemIn),
        required=True,
        validate=validate.Length(min=1, max=100),
    )

    @validates_schema
    def _no_duplicate_products(self, data, **kwargs):
        ids = [item["product_id"] for item in data.get("items", [])]
        if len(ids) != len(set(ids)):
            raise ValidationError("product_id must be unique within an order.", "items")


class OrderItemOut(Schema):
    id = fields.Int()
    product_id = fields.Int()
    qty = fields.Int()
    unit_price_cents = fields.Int()
    line_total_cents = fields.Int()
    product = fields.Nested(ProductBrief)


class OrderOut(Schema):
    id = fields.Int()
    customer_name = fields.Str()
    created_at = fields.DateTime()
    items = fields.Nested(OrderItemOut, many=True)
    total_cents = fields.Int()


ORDER_OUT = OrderOut()
ORDER_OUT_MANY = OrderOut(many=True)