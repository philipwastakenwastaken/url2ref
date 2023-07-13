from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
import pycountry

language_list = [x.alpha_2 for x in list(pycountry.languages) if hasattr(x, 'alpha_2')]
langs = [(i+1, language_list[i])
        for i in range(len(language_list))]

class UrlInputForm(FlaskForm):
    url_field = StringField('URL', validators=[DataRequired()])
    targ_lang_field = SelectField('Target language', default=37, choices=langs, validators=[DataRequired(), Length(min=2, max=2)])
    src_lang_field  = SelectField('Source language', default=0, choices=[(0, 'auto detect')]+langs, validators=[DataRequired(), Length(min=2, max=2)])
    submit = SubmitField('Generate')
