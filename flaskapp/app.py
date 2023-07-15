from flask import Flask, render_template, flash
from url2ref import url2ref
from .url import UrlInputForm
from flask_assets import Environment, Bundle

import os


app = Flask(__name__)
# Setting random secret key to prevent:
#   RuntimeError: A secret key is required to use CSRF.
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY


# Compiling Bootstrap files according to the following guide:
# https://edaoud.com/blog/2022/02/07/flask-bootstrap-assets/
assets = Environment(app)
assets.url = app.static_url_path

js = Bundle(
    "assets/node_modules/@popperjs/core/dist/umd/popper.min.js",
    "assets/node_modules/bootstrap/dist/js/bootstrap.min.js",
    "assets/custom.js",
    filters="jsmin",
    output="js/generated.js"
)
assets.register("js_all", js)

scss = Bundle(
    "assets/main.scss",
    filters="libsass", # https://webassets.readthedocs.io/en/latest/builtin_filters.html#libsass
    output="css/scss-generated.css"
)
assets.register("scss_all", scss)


@app.route("/", methods=['GET', 'POST'])
def home():
    form = UrlInputForm()
    if form.validate_on_submit():
        res = url2ref(url=form.url_field.data, 
                      src_lang=form.src_lang_field.data, 
                      targ_lang=form.targ_lang_field.data)
        flash(res, 'success')
    return render_template('home.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)