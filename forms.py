from flask_wtf import FlaskForm
from wtforms import SubmitField,FileField,StringField,SelectField
from wtforms.validators import DataRequired

class ColorForm(FlaskForm):
    color = FileField(validators=[DataRequired("This field is required")])
    submit = SubmitField()

class GifForm(FlaskForm):
    frame = StringField(validators=[DataRequired("This field is required")])
    submit = SubmitField()
