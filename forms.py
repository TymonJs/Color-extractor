from flask_wtf import FlaskForm
from wtforms import SubmitField,FileField
from wtforms.validators import DataRequired

class ColorForm(FlaskForm):
    color = FileField("Choose an image to process", validators=[DataRequired("This field is required")])
    submit = SubmitField("Submit Post")
