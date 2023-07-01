from flask import Flask, render_template, flash
from url2ref import url2ref
from .url import UrlInputForm

import os


app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

@app.route("/", methods=['GET', 'POST'])
def home():
    form = UrlInputForm()
    if form.validate_on_submit():
        flash(f'Reference: {url2ref(form.field.data)}', 'success')
    return render_template('home.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)