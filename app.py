from flask import Flask, jsonify, request, render_template, url_for, redirect, flash, get_flashed_messages, session as flask_session
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import joinedload
from extenstions import LoginManager, current_user, login_user
from database import get_session
from objects import Customer, Order, Product, OrderItem
from forms import CustomerForm, ProductForm, OrderForm, OrderItemForm, LoginForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "Slighting-Speckled9-Hypnotist-Tranquil-Marital"
csrf = CSRFProtect(app)
login = LoginManager(app)

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        with get_session() as session:
            customer = session.query(Customer).where(Customer.email == form.email.data)
            if customer is None or not customer.check_password(form.password.data):
                flash('Invalid username or password')
                return redirect(url_for('login'))
            login_user(customer, remember=form.remember_me.data)
            return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

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
        # Only get active customers
        customers = session.query(Customer).filter(Customer.active == True).all()
    
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
            customer_id = customer.id

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


    return render_template("edit_customer.html", form=form, name=customer_name or form.name.data, id=customer_id) # Edit html to use customer var only?

@app.route('/customers', methods=['POST'])
def create_customer():
    data = request.json
    with get_session() as session:
        customer = Customer(name=data['name'], email=data['email'])
        session.add(customer)
        session.commit()
        customer_data = serialise(customer)
    return jsonify(customer_data), 201

# Delete a customer
@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    with get_session() as session:
        customer = session.query(Customer).get(customer_id)
        if not customer:
            flash("Customer not found", "error")
            return redirect(url_for("get_customers"))
        
        # Soft delete - just mark as inacticve
        customer.active = False

        flash(f"Customer {customer.name} has been deleted", "success")
        return redirect(url_for("get_customers")) 
    
# View deleted customers
@app.route("/customers/deleted", methods=["GET"])
def get_deleted_customers():
    with get_session() as session:
        deleted_customers = session.query(Customer).filter(Customer.active == False).all()
        return render_template("deleted_customers.html", title="Deleted Customers", customers=deleted_customers)

# Restore a deleted customer
@app.route("/customers/<int:customer_id>/restore", methods=["GET","POST"])
def restore_customer(customer_id):
    with get_session() as session:
        customer = session.query(Customer).get(customer_id)
        if not customer:
            flash("Customer not found", "error")
            return redirect(url_for("get_customers"))
        
        customer.active = True

        flash(f"Customer {customer.name} has been restored successfully", "success")
        return redirect(url_for("get_customers"))

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
        products = session.query(Product).filter(Product.active==True).all()
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

# Add product via HTML
@app.route("/products/add", methods=["GET", "POST"])
def create_new_product():
    form = ProductForm()

    if request.method == "POST":
        if form.validate_on_submit():
            with get_session() as session:
                product = Product(name=form.name.data,
                                price=form.price.data)
                session.add(product)
            flash("Product added successfully", "success")
            return redirect(url_for("get_products"))
        
        else:
            flash("Validation failled", form.errors)

    return render_template("add_product.html", title="Add Product", form=form)

# Edit product
@app.route("/products/<int:product_id>/edit", methods = ["GET", "POST"])
def edit_product(product_id):
    form = ProductForm()

    # Load page - GET request
    if request.method == "GET":
        with get_session() as session:
            product = session.query(Product).get(product_id)
            if not product:
                flash("Product not found", "error")
                return redirect(url_for("get_products"))

            form.name.data = product.name
            form.price.data = product.price
            id = product.id

    # Handle submission
    if form.validate_on_submit():
        try:
            with get_session() as session:
                product = session.query(Product).get(product_id)
                if not product:
                    flash("Product not found", "error")
                    return redirect(url_for("products"))
                
                product.name = form.name.data
                product.price = form.price.data

                flash("Updated successfully", "success")
                return redirect(url_for("get_products"))
            
        except Exception as e:
            flash(f"Error updating product: {e}", "error")
            return redirect(url_for("get_products"))
        
    return render_template("edit_product.html", title="Edit Product", form=form, id=id)

# Delete product
@app.route("/products/<int:product_id>/delete", methods=["GET", "POST"])
def delete_product(product_id):
    with get_session() as session:
        product = session.query(Product).get(product_id)
        if not product:
            flash("Product not found", "error")
            return redirect(url_for("get_products"))
        
        product.active = False
        flash(f"Product '{product.name}' has been deleted", "success")

        return redirect(url_for("get_products"))

# View deleted products
@app.route("/products/deleted", methods=["GET"])
def get_deleted_products():
    with get_session() as session:
        products = session.query(Product).filter(Product.active == False).all()
        return render_template("deleted_products.html", title="Deleted Products", products=products) 

# Restore a deleted product
@app.route("/products/<int:product_id>/restore")
def restore_product(product_id):
    with get_session() as session:
        product = session.query(Product).get(product_id)
        if not product:
            flash("Product not found", "error")
            return redirect(url_for("get_products"))
        
        product.active = True
        flash(f"Product '{product.name}' successfully restored", "success")
        return redirect(url_for("get_products"))
    
# View product orders
@app.route("/products/<int:product_id>/orders", methods=["GET"])
def get_product_orders(product_id):
    with get_session() as session:
        orders = session.query(Order).filter(Order.items.product_id == product_id).options(joinedload(Order.items)).all()
        if not orders:
            flash("No orders associated with this product", "error")
            return redirect(url_for("get_products"))
        
        return render_template("product_orders.html", Title="Product Orders", orders=orders)

# routes for orders
# Get all orders
@app.route("/orders", methods=["GET"])
def get_orders():
    with get_session() as session:
        orders = session.query(Order).options(joinedload(Order.customer)).options(joinedload(Order.items)).all()
        orders_data = [serialise(order) for order in orders]
        session.close()

    if request.args.get("format") == "json" or request.headers.get("Accept") == "application/json":
        return jsonify(orders_data)
    else:
        return render_template("orders.html", title="Orders", orders=orders)

# Get one order
@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    with get_session() as session:
        order = session.query(Order).get(order_id)
        session.close()

        if order:
            return jsonify(serialise(order))
    return jsonify({"error" : "Unable to find order"}), 404

# Create new order
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

# Create a new order (HTML)
@app.route("/orders/<int:customer_id>/add_order", methods =["GET", "POST"])
def add_order(customer_id):
    # Verify customer exists
    with get_session() as session:
        customer = session.query(Customer).get(customer_id)
        if not customer:
            flash("Customer not found", "error")
            return redirect(url_for("get_orders"))

        # Prepare product selection
        products = session.query(Product).filter_by(active=True).all()

        # Initialise the order item form
        item_form = OrderItemForm()
        item_form.product_id.choices = [(p.id, f"{p.name} (${p.price:.2f})") for p in products]

        customer_name = customer.name

    # Initialise flask session for order items
    if "order_items" not in flask_session:
        flask_session["order_items"] = []

    # Handle adding an item to the order
    if request.method == "POST" and "add_item" in request.form:
        if item_form.validate_on_submit():
            with get_session() as session:
                product = session.query(Product).get(item_form.product_id.data)

                flask_session["order_items"].append({
                    "product_id":product.id,
                    "product_name":product.name,
                    "price":product.price,
                    "quantity":item_form.quantity.data,
                    "subtotal":product.price * item_form.quantity.data
                })

                flash(f"Added {item_form.quantity.data} x {product.name}", "success")

        else:
            flash("Please select a product and a quantity", "error")

        return redirect(url_for("add_order", customer_id=customer_id))

    # Handle completing the order
    if request.method == "POST" and "complete_order" in request.form:
        # Validate that we have items
        if not flask_session.get("order_items", []):
            flash("Cannot create empty order", "error")
            return redirect(url_for("add_order", customer_id=customer_id))

        try:
            with get_session() as session:
                # Create new order
                new_order = Order(customer_id=customer_id)
                session.add(new_order)
                session.flush() # makes new order ID available

                # Add order items
                for item in flask_session["order_items"]:
                    order_item = OrderItem(
                        order_id=new_order.id,
                        product_id=item["product_id"],
                        quantity=item["quantity"]
                    )
                    session.add(order_item)

                session.commit()

                # Clear Flask session order items
                flask_session.pop("order_items", None)
                flash("Order created successfully", "success")
                return redirect(url_for("get_orders"))

        except Exception as e:
            flash(f"Error creating order: {e}", "error")
            return redirect(url_for("add_order", customer_id=customer_id))

    # Calculate order total
    order_total = sum(item["subtotal"] for item in flask_session.get("order_items", []))

    return render_template(
        "add_order.html", 
        title=f"Create Order for {customer_name}",
        customer_name=customer_name,
        customer=customer,
        item_form=item_form,
        items=flask_session.get('order_items', []),
        order_total=order_total
    )

# View order
@app.route("/orders/view/<int:order_id>", methods=["GET"])
def view_order(order_id):
    # Query order
    with get_session() as session:
        order_items = (session.query(OrderItem)
                       .options(joinedload(OrderItem.product))
                       .filter_by(order_id=order_id)
                       .all())
        
        if not order_items:
            flash("Order does not exist", "error")
            return redirect(url_for("get_orders"))
        '''order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            flash("Order does not exist", "error")
            return redirect(url_for("get_orders"))
        
        # Query orderitems
        order_items = session.query(OrderItem).filter_by(order_id=order_id).all()
        items = order_items'''

        return render_template("view_order.html", title=f"Order #{order_id}", items=order_items)

# Run the flask app
if __name__ == "__main__":
    app.run(debug=True)