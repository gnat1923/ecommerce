# Ecommerce database app

Testing the use of Flask and SQLAlchemy for use in an ecommerce database

## HTML
The Flask app can be served over HTML by launching the app `python3 app.py`and connecting to the local server on the browser.

## Terminal / .json commands
The database can also be interacted with via the terminal

### Terminal GET request examples
Fetch data for all customers:
`curl http://127.0.0.1:5000/customers`

Fetch a specific customer (by ID):
`curl http://127.0.0.1:5000/customers/1`

Create a product:
`curl -X POST -H "Content-Type: application/json" -d '{"name": "Laptop", "price": 1200.00}' http://127.0.0.1:5000/products
curl -X POST -H "Content-Type: application/json" -d '{"name": "Headphones", "price": 150.00}' http://127.0.0.1:5000/products`

Create an order:
`curl -X POST -H "Content-Type: application/json" -d '{
  "customer_id": 1,
  "items": [
    {"product_id": 1, "quantity": 1},
    {"product_id": 2, "quantity": 2}
  ]
}' http://127.0.0.1:5000/orders`