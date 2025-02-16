from flask import Flask, jsonify, request
from database import get_session
from objects import Customer, Order, Product, OrderItem

app = Flask(__name__)

# Helper function to serialise SQLAlchemy objects
def serialise(obj):
    if isinstance(obj, Customer):
        return {
            "id": obj.id,
            "name" : obj.name,
            "email" : obj.email
        }
    elif isinstance(obj, Order):
        return {
            "id" : obj.id,
            "customer_id" : obj.customer_id,
            "items" : [serialise(item) for item in obj.items]
        }
    elif isinstance(obj, Product):
        return {
            "id" : obj.id,
            "name" : obj.name,
            "price" : obj.price
        }
    elif isinstance(obj, OrderItem):
        return {
            "id" : obj.id,
            "order_id" : obj.order_id,
            "product_id" : obj.product_id,
            "quantity" : obj.quantity
        }
    return {}

# Routes for customers
@app.route("/customers", methods=["GET"])
def get_customers():
    session = get_session()
    customers = session.query(Customer).all()
    session.close()
    return jsonify([serialise(customer) for customer in customers])

@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    session = get_session()
    customer = session.query(Customer).get(customer_id)
    session.close()

    if customer:
        return jsonify(serialise(customer))
    return jsonify({"error": "Customer not found"}), 404

@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.json
    session = get_session()
    customer = Customer(name = data["name"], email = data["email"])
    session.add(customer)
    session.commit()
    session.close()

    return jsonify(serialise(customer)), 201

# Routes for products
@app.route("/products", methods=["GET"])
def get_products():
    session = get_session()
    products = session.query(Product).all()
    session.close()
    return jsonify([serialise(product) for product in products])

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    session = get_session()
    product = session.query(Product).get(product_id)
    session.close()

    if product:
        return jsonify(serialise(product))
    return jsonify({"error" : "Product not found"}), 404

@app.route("/products", methods=["POST"])
def create_product():
    data = request.json
    session = get_session()
    product = Product(name=data["name"], price=data["price"])
    session.add(product)
    session.commit()
    session.close()
    return jsonify(serialise(product)), 201

# routes for orders
@app.route("/orders", methods=["GET"])
def get_orders():
    session = get_session()
    orders = session.query(Order).all()
    session.close()
    return jsonify([serialise(order) for order in orders])

@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    session = get_session()
    order = session.query(Order).get(order_id)
    session.close()

    if order:
        return jsonify(serialise(order))
    return jsonify({"error" : "Unable to find order"}), 404

@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json
    session = session.get()
    order = Order(customer_id=data["customer_id"])
    for item in data["items"]:
        order_item = OrderItem(product_id=item["product_id"], quantity=item["quantity"])
        order.items.append(order_item)
    
    session.add(order)
    session.commit()
    session.close()
    return jsonify(serialise(order)), 201

# Run the flask app
if __name__ == "__main__":
    app.run(debug=True)