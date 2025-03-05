from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, FloatField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange

class CustomerForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Save")

class ProductForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired()])
    submit = SubmitField("Save")

class OrderForm(FlaskForm):
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    submit = SubmitField("Create Order")

class OrderItemForm(FlaskForm):
    product_id = SelectField("Product", coerce=int, validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)])
    add_item = SubmitField("Add Item")