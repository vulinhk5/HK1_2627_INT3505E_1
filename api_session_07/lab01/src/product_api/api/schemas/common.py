from marshmallow import ValidationError, fields

INT_MAX = 2_147_483_647  

def not_blank(value: str) -> None:
    if not value.strip():
        raise ValidationError("must not be blank.")


def strict_int(**kwargs):
    return fields.Int(strict=True, **kwargs)