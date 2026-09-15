from flask import Flask, jsonify
app = Flask(__name__)

#mock data
ORDERS = {
    "ord-01": {"id": "ord-01", "item": "pencil", "status": "pending"},     
    "ord-02": {"id": "ord-02", "item": "shirt", "status": "shipped"},     
    "ord-03": {"id": "ord-03", "item": "lightstick", "status": "delivered"}     
}
@app.route("/orders/<order_id>", methods=["DELETE"])
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

if __name__ == "__main__":
    app.run(debug=True)