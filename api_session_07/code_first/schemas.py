from marshmallow import Schema, fields, validate

class ProductInSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    description = fields.String(allow_none=True, load_default=None)


class ProductSchema(ProductInSchema):
    id = fields.Integer(dump_only=True)