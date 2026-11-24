import itertools

_seq = itertools.count(1)


def v1_create_order(body):
    return {
        "order_id": f"v1-{next(_seq)}",
        "account_id": body.get("account_id"),
        "handler": "v1",
    }

def v2_create_order(body):
    return {
        "order_id": f"v2-{next(_seq)}",
        "account_id": body.get("account_id"),
        "handler": "v2",
    }
