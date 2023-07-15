from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
import pycountry

language_list = [(x.alpha_2, x.name) for x in list(pycountry.languages) if hasattr(x, 'alpha_2')]
langs = [(language_list[i][0], language_list[i][1])
        for i in range(len(language_list))]

class UrlInputForm(FlaskForm):
    url_field = StringField('URL', validators=[DataRequired()])
    targ_lang_field = SelectField('Target language', default='en', choices=langs, validators=[DataRequired(), Length(min=2, max=2)])
    src_lang_field  = SelectField('Source language', default='auto', choices=[('auto', 'Autodetect')]+langs, validators=[DataRequired()])
    submit = SubmitField('Generate')
