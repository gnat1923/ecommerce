from flask import Flask, jsonify, request, render_template
from sqlalchemy.orm import joinedload
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

# Homepage
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Routes for customers
@app.route("/customers", methods=["GET"])
def get_customers():
    with get_session() as session:
        # Eager load the orders relationship so html can access it
        customers = session.query(Customer).options(joinedload(Customer.orders)).all()
        session.close()
    
    # differentiate between .json and html requests
    if request.args.get("format") == "json" or request.headers.get("Accept") == "application/json":
        return jsonify([serialise(customer) for customer in customers])
    else:
        return render_template("customers.html", title="Customers - ", customers=customers)
    

@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    with get_session() as session:
        customer = session.query(Customer).get(customer_id)
        session.close()

        if customer:
            return jsonify(serialise(customer))
    return jsonify({"error": "Customer not found"}), 404

@app.route('/customers', methods=['POST'])
def create_customer():
    data = request.json
    with get_session() as session:
        customer = Customer(name=data['name'], email=data['email'])
        session.add(customer)
        session.commit()
        customer_data = serialise(customer)
    return jsonify(customer_data), 201

# Routes for products
@app.route("/products", methods=["GET"])
def get_products():
    with get_session() as session:
        products = session.query(Product).all()
        products_data = [serialise(product) for product in products]
        session.close()

    if request.args.get("format") == "json" or request.headers.get("Accept") == "application/json":
        return jsonify(products_data)
    else:
        return render_template("products.html", title="Products - ", products=products)

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    with get_session() as session:
        product = session.query(Product).get(product_id)
        session.close()

        if product:
            return jsonify(serialise(product))
    return jsonify({"error" : "Product not found"}), 404

@app.route("/products", methods=["POST"])
def create_product():
    data = request.json
    with get_session() as session:
        product = Product(name=data["name"], price=data["price"])
        session.add(product)
        session.commit()
        product_data = serialise(product)
        #session.close()
    return jsonify(product_data), 201

# routes for orders
@app.route("/orders", methods=["GET"])
def get_orders():
    with get_session() as session:
        orders = session.query(Order).options(joinedload(Order.customer)).options(joinedload(Order.items)).all()
        orders_data = [serialise(order) for order in orders]
        session.close()

    if request.args.get("format") == "json" or request.headers.get("Accept") == "application/json":
        return jsonify(orders_data)
    else:
        return render_template("orders.html", title="Orders - ", orders=orders)

@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    with get_session() as session:
        order = session.query(Order).get(order_id)
        session.close()

        if order:
            return jsonify(serialise(order))
    return jsonify({"error" : "Unable to find order"}), 404

@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json
    with get_session() as session:
        order = Order(customer_id=data["customer_id"])
        session.add(order)
        session.commit() # Add order so we can access order.id

        # Add order items
        for item in data["items"]:
            order_item = OrderItem(
                order_id = order.id,
                product_id=item["product_id"], 
                quantity=item["quantity"])
            session.add(order_item)
        session.commit()

        order_data = {
            "id" : order.id,
            "customer_id" : order.customer_id,
            "items": [
                {"product_id" : item.product_id, "quantity" : item.quantity}
                for item in order.items
            ]
        }

    return jsonify(order_data), 201

# Run the flask app
if __name__ == "__main__":
    app.run(debug=True)