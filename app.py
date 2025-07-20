from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']   = 'sqlite:///customers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Customer(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(120), nullable=False)
    email   = db.Column(db.String(120), nullable=False, unique=True)
    country = db.Column(db.String(120))
    city    = db.Column(db.String(120))
    mobile  = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'id'     : self.id,
            'name'   : self.name,
            'email'  : self.email,
            'country': self.country,
            'city'   : self.city,
            'mobile' : self.mobile
        }

@app.route('/customers', methods=['POST'])
def add_customer():
    data = request.get_json(force=True)
    name, email, mobile = data.get('name'), data.get('email'), data.get('mobile')
    country, city       = data.get('country'), data.get('city')

    if not name or not email or not mobile:
        return jsonify({'error': 'Name, email, and mobile are required.'}), 400

    customer = Customer(
        name=name, email=email,
        country=country, city=city,
        mobile=mobile
    )
    db.session.add(customer)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Email must be unique.'}), 400

    return jsonify({'message': 'Customer added successfully.',
                    'customer': customer.to_dict()}), 201

@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([c.to_dict() for c in customers]), 200

if __name__ == '__main__':
    # Create tables before handling any requests
    with app.app_context():
        db.create_all()

    # Start the server
    app.run(debug=True)
