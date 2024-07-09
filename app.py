from flask import Flask, abort, flash, redirect, render_template, request, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, login_user, logout_user, login_required

from loginSignup import Login
from TradingSignals import tradingsignals




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Nill!6992@cedartrading.chyem684wzw8.us-east-1.rds.amazonaws.com:5432/cedartrading'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

app.secret_key = 'nil123'

class TradingSignal(db.Model):
    __tablename__ = 'trading_signal'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    buy = db.Column(db.String, nullable=False)
    target = db.Column(db.String, nullable=False)
    sl = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, default='Pending')
    indexName = db.Column(db.String, nullable=False)
    IndexToken = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'<Trading Signal {self.name}>'

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))  # Adjusted for length as per previous discussion

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)  # convert the id to a string

    def __repr__(self):
        return f'<User {self.username}>'



@app.route('/api/trading_signal', methods=['POST'])
def add_trading_signal():
    data = request.json
    new_signal = TradingSignal(
        name=data['name'],
        buy=data['buy'],
        target=data['target'],
        sl=data['sl'],
        status=data['Status'],
        indexName=data['indexName'],
        IndexToken=data['IndexToken']
    )
    db.session.add(new_signal)
    db.session.commit()
    return jsonify({'message': 'Trading signal added', 'id': new_signal.id}), 201

@app.route('/api/user', methods=['POST'])
def add_user():
    email = request.form.get('username')
    if email:
        new_user = User(username="Prelaunch", email=email)
        db.session.add(new_user)
        db.session.commit()
        flash('Thank you for subscribing!', 'success')
    else:
        flash('Please enter a valid email address.', 'error')
    return redirect(url_for('home'))

@app.route('/api/trading_signals', methods=['GET'])
def get_trading_signals():
    signals = TradingSignal.query.all()
    results = [{
        'id': signal.id,
        'name': signal.name,
        'buy': signal.buy,
        'target': signal.target,
        'sl': signal.sl,
        'status': signal.status,
        'indexName': signal.indexName,
        'IndexToken': signal.IndexToken
    } for signal in signals]
    return jsonify(results), 200

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    results = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
    } for user in users]
    return jsonify(results), 200

@app.route('/api/trading_signal/<int:id>/edit_status', methods=['PATCH'])
def edit_trading_signal_status(id):
    data = request.json
    trading_signal = TradingSignal.query.get(id)
    if not trading_signal:
        abort(404, description="Trading Signal not found.")
    
    if 'status' in data:
        trading_signal.status = data['status']
        db.session.commit()
        return jsonify({'message': 'Trading signal status updated', 'id': trading_signal.id}), 200
    else:
        abort(400, description="No status provided.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/Blog')
def Blog():
    return render_template('BlogPage.html')

@app.route('/HomePage')
def HomePage():

    TradingData = tradingsignals.GetTradingSignals.TradingSignals()
    return render_template('HomePage.html',trading_data=TradingData)



@app.route('/signupreq', methods=['POST'])
def signupReq():
    data = request.form
    SignUPData = Login.LoginPage.signup(data,User)
    if SignUPData == "Email address already exists":
        return SignUPData
    else:
        db.session.add(SignUPData)
        db.session.commit()
        login_user(SignUPData)
        return redirect(url_for('HomePage'))
    
@app.route('/loginreq', methods=['POST'])
def loginReq():
    data = request.form
    LoginData = Login.LoginPage.login(data,User)
    if LoginData == "Wrong Username Or Password":
         return "Wrong Username or Password"
    else:
         login_user(LoginData)
         return redirect(url_for('HomePage'))


@app.route('/api/stock/<int:id>', methods=['DELETE'])
def delete_stock(id):
    stock = TradingSignal.query.get_or_404(id)
    db.session.delete(stock)
    db.session.commit()
    return jsonify({'message': 'Stock deleted successfully'}), 200

# @app.route('/api/stock', methods=['DELETE'])
# def delete_all_stocks():
#     try:
#         # Fetch all trading signals from the database
#         all_stocks = TradingSignal.query.all()
        
#         # Check if there are any trading signals to delete
#         if not all_stocks:
#             return jsonify({'message': 'No stocks to delete'}), 404
        
#         # Delete all trading signals
#         for stock in all_stocks:
#             db.session.delete(stock)
        
#         # Commit the changes to the database
#         db.session.commit()
        
#         return jsonify({'message': 'All stocks deleted successfully'}), 200
#     except Exception as e:
#         # Handle exceptions and return an error message
#         return jsonify({'error': 'Failed to delete stocks', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
