from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, FloatField, SubmitField
from wtforms.validators import DataRequired, Email

class CustomerForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    submit = SubmitField("Save")

class ProductForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired()])
    submit = SubmitField("Save")