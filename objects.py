from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extenstions import login
from database import Base, Session

@login.user_loader
def load_user(id):
    session = Session()
    return session.get(Customer, int(id))

# Define the customer table
class Customer(UserMixin, Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    active = Column(Boolean, default=True)
    password_hash = Column(String, nullable=True)
    orders = relationship("Order", back_populates="customer")

    def set_password(self, password):
        '''Sets the Customer password'''
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        '''Checks the provided password matches the hash stored in the db'''
        return check_password_hash(self.password_hash, password)

# Define the order table
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

# Define product table
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    items = relationship("OrderItem", back_populates="product")

# Define the OrderItem table (many-to-many relationship between orders and products)
class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="items")
