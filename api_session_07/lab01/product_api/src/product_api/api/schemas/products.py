from marshmallow import Schema, fields, validate

from .common import INT_MAX, not_blank, strict_int


class ProductOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()
    created_at = fields.DateTime()


class ProductIn(Schema):

    sku = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(required=True, validate=[validate.Length(min=1, max=255), not_blank])
    description = fields.Str(
        load_default=None, allow_none=True, validate=validate.Length(max=2000)
    )
    price_cents = strict_int(required=True, validate=validate.Range(min=0, max=INT_MAX))
    qty_in_stock = strict_int(load_default=0, validate=validate.Range(min=0, max=INT_MAX))


class ProductPatch(Schema):
    name = fields.Str(validate=[validate.Length(min=1, max=255), not_blank])
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    price_cents = strict_int(validate=validate.Range(min=0, max=INT_MAX))
    qty_in_stock = strict_int(validate=validate.Range(min=0, max=INT_MAX))


class ReserveIn(Schema):

    qty = strict_int(required=True, validate=validate.Range(min=1, max=INT_MAX))


class ProductBrief(Schema):

    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()

PRODUCT_OUT = ProductOut()
PRODUCT_OUT_MANY = ProductOut(many=True)
