from flask import Flask, jsonify
ORDERS = {}

@app.route("/orders/<id>", methods=["DELETE"])
def delete_order(order_id):
    order = ORDERS.get(order_id)

    if order is None:
        return {
            "error": "Order not found"
        }, 404

    if order["status"] in ["shipped", "delivered"]:
        return {
            "error": "Cannot delete an order that has already been shipped or delivered"
        }, 409

    ORDERS.pop(order_id, None)
    return {}, 204