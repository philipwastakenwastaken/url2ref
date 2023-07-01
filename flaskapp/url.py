from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class UrlInputForm(FlaskForm):
    field = StringField('URL', validators=[DataRequired()])
    #TODO: Validate input
    submit = SubmitField('Fetch')
