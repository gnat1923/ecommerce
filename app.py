from flask import Flask, jsonify, request, render_template, url_for, redirect, flash, get_flashed_messages
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import joinedload
from database import get_session
from objects import Customer, Order, Product, OrderItem
from forms import CustomerForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "Slighting-Speckled9-Hypnotist-Tranquil-Marital"
csrf = CSRFProtect(app)

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

# Add customer
@app.route("/customers/add", methods = ["GET", "POST"])
def add_new_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        print("Form submitted successfully") # debugging
        with get_session() as session:
            customer = Customer(name=form.name.data,
                                email=form.email.data)
            session.add(customer)
        return redirect(url_for("get_customers"))
    else:
        print("Validation failled", form.errors)
    
    return render_template("add_customer.html", form=form)

# Routes for customers
@app.route("/customers", methods=["GET"])
def get_customers():
    with get_session() as session:
        # Eager load the orders relationship so html can access it
        customers = session.query(Customer).all()
    
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

# Edit customers
@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
def edit_customer(customer_id):
    form = CustomerForm()
    customer_name = ""

    # Handle GET request + populate form
    if request.method == "GET":
        with get_session() as session:
            customer = session.query(Customer).get(customer_id)
            if not customer:
                flash("Customer not found", "error")
                return redirect(url_for("get_customers"))
            
            form.name.data = customer.name
            form.email.data = customer.email
            customer_name = customer.name

    # Handle POST request
    if form.validate_on_submit() and request.method == "POST":
        try:
            with get_session() as session:
                customer = session.query(Customer).get(customer_id)
                if not customer:
                    flash("Customer not found", "error")
                    return redirect(url_for("get_customers"))
                
                customer.name = form.name.data
                customer.email = form.email.data

                flash("Updated successfully", "success")
                return redirect(url_for("get_customers"))
        
        except Exception as e:
            # The context manager will handle rollback
            flash(f"Error updating customer: {str(e)}", "error")
            return redirect(url_for("get_customers"))

    '''with get_session() as session:
        customer = session.query(Customer).get(customer_id)
        name = customer.name
        email = customer.email

    if request.method == "GET":
        # Populate the form
        form.name.data = name
        form.email.data = email

    if form.validate_on_submit() and request.method == "POST":
    #if form.validate_on_submit():
    
        try:
            with get_session() as session:
                customer.name = form.name.data
                customer.email = form.email.data
                session.commit()
                return redirect(url_for("get_customers"))
            
        except Exception as e:
            print("An error occured")
            return redirect(url_for("get_customers"))'''


    return render_template("edit_customer.html", form=form, name=customer_name or form.name.data)

@app.route('/customers', methods=['POST'])
def create_customer():
    data = request.json
    with get_session() as session:
        customer = Customer(name=data['name'], email=data['email'])
        session.add(customer)
        session.commit()
        customer_data = serialise(customer)
    return jsonify(customer_data), 201

# View customer orders
@app.route("/customers/<int:customer_id>/orders", methods=["GET"])
def get_customer_orders(customer_id):
    with get_session() as session:
        customer_orders = session.query(Order).filter(Order.customer_id == customer_id).options(joinedload(Order.customer)).all()
        session.close()

        if customer_orders:
            for order in customer_orders:
                print(f"Order ID; {order.id}")
            return render_template("customer_orders.html", title="Customer Order(s) - ", customer_orders=customer_orders)
        else:
            return 404

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