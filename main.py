import os

from flask import Flask, render_template, request, url_for, jsonify, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, URL, Length

from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donz'
Bootstrap(app)



##Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
# this has to be turned off to prevent flask-sqlalchemy framework from tracking events and save resources
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# I have to create this key to use CSRF protection for form
db = SQLAlchemy(app)

class Cafe(db.Model):
    # base class to inherit when we create our db entities
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.Date, default=date.today())

    name = db.Column(db.String(250), unique=True, nullable=False)
    location = db.Column(db.String(250), nullable=False)
    # img_url = db.Column(db.String(500), nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)
    has_wifi = db.Column(db.Boolean)

    # I just want to return a string with custom printable representation of an object, overrides standard one
    def __repr__(self):
        return f'<Cafe: {self.id}>'

    def to_dict(self):
        dictionary = {}
        # Loop through each column of cafe table in the data record
        for column in self.__table__.columns:
            # Create a new dictionary entry;
            # where the key is the name of the column
            # and the value is the value of the column
            dictionary[column.name] = getattr(self, column.name)
        return dictionary

@app.before_first_request
def before_first_request():
    db.create_all()

def ch_list_gen(symbol: str):
    return [symbol*_ if _ != 0 else ' ' for _ in range(6)]


class CafeForm(FlaskForm):
    name_f = StringField(label='Cafe name', validators=[DataRequired(), Length(min=2, max=30)])
    location_f = StringField(label='Location', validators=[DataRequired()])
    # img_url_f = StringField(label='Photo', validators=[DataRequired()])
    coffee_price_f = SelectField(label='Price', choices=ch_list_gen('💲'), validators=[DataRequired()])
    has_wifi_f = BooleanField(label='Has Wi-Fi?', render_kw={'value': 1})

    submit_f = SubmitField(label='Submit')


@app.route("/")
def index():
    # get last 3 cafes from the database
    cafes3 = db.session.query(Cafe).order_by(Cafe.id.desc()).limit(3)
    return render_template("index.html", cafes=cafes3)


@app.route("/add", methods=['GET', 'POST'])
def add_cafe():
    form = CafeForm()
    # check if it's a valid POST request
    if form.validate_on_submit():
        new_cafe = Cafe()
        new_cafe.name = request.form.get('name_f')
        new_cafe.location = request.form.get('location_f')
        # new_cafe.img_url = request.form.get('img_url_f')
        new_cafe.coffee_price = request.form.get('coffee_price_f')
        new_cafe.has_wifi = int(request.form.get('has_wifi_f'))
        print(request.form.get('has_wifi_f'))
        try:
            db.session.add(new_cafe)
            db.session.commit()
            return redirect(url_for('get_all'))
        except:
            return jsonify(response={"error": "Couldn't add cafe to the database. "})
    else:
        return render_template("add.html", form=form)

@app.route("/all")
def get_all():
    cafes = db.session.query(Cafe).all()
    cafes_list = [cafe.to_dict() for cafe in cafes]
    return render_template('all.html', cafes=cafes_list)


@app.route("/cafes/<int:cafe_id>", methods=['GET', 'POST'])
def edit(cafe_id):
    # same as Cafe.query.get(cafe_id)
    cafe_to_edit = db.session.query(Cafe).get(cafe_id)
    form = CafeForm(name_f=cafe_to_edit.name,
                    location_f=cafe_to_edit.location,
                    coffee_price_f=cafe_to_edit.coffee_price,
                    has_wifi_f=int(cafe_to_edit.has_wifi))
    # form.img_url_f = cafe_to_edit.img_url
    if form.validate_on_submit():
        cafe_to_edit.name = request.form.get('name_f')
        cafe_to_edit.location = request.form.get('location_f')
        # cafe_to_edit.img_url = request.form.get('img_url_f')
        cafe_to_edit.coffee_price = request.form.get('coffee_price_f')
        # cafe_to_edit.has_wifi = int(request.form.get('has_wifi_f'))
        try:
            db.session.commit()
            return redirect(url_for('get_all'))
        except:
            return jsonify(response={"error": "Couldn't update the cafe. "}), 404
    else:
        return render_template('cafe.html', form=form, cafe=cafe_to_edit)

@app.route("/delete/<int:cafe_id>")
def delete(cafe_id):
    cafe_to_delete = db.session.query(Cafe).get(cafe_id)
    if cafe_to_delete:
        try:
            db.session.delete(cafe_to_delete)
            db.session.commit()
            return redirect(url_for('get_all'))
        except:
            return jsonify(response={"error": "Couldn't delete the cafe. "}), 404
    else:
        return jsonify(response={"error": "Couldn't find the cafe. "}), 404

if __name__ == '__main__':
    app.run()
# debug=True