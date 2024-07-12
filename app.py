import os
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import razorpay

from loginSignup import Login

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Nill!6992@cedartrading.chyem684wzw8.us-east-1.rds.amazonaws.com:5432/cedartrading'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "nil123"
app.config['PREFERRED_URL_SCHEME'] = 'https'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

client = razorpay.Client(auth=("rzp_test_2hY8PR8G5rKybf", "E8w1YuPcAesivzTuSY5Y87qF"))

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))
    subscription_end_date = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True

    @property
    def is_active(self):
        """User is active if their subscription has not expired or is not set (None)."""
        if self.subscription_end_date is None:
            return False  # If no end date, consider the user always active.
        return self.subscription_end_date > datetime.now()

    @property
    def is_anonymous(self):
        """Always return False, as anonymous users aren't supported."""
        return False

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return str(self.id) 

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

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(User, int(user_id))



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
        print('Thank you for subscribing!', 'success')
    else:
        print('Please enter a valid email address.', 'error')
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
@login_required
def HomePage():
    trading_data = {}
    signals = TradingSignal.query.all()  # Assuming this fetches all trading signals
    for signal in signals:
        if signal.indexName not in trading_data:
            trading_data[signal.indexName] = []
        trading_data[signal.indexName].append(signal)

    if not User.is_active:
        print('Your subscription has expired. Please renew.', 'warning')
        return redirect(url_for('subscribe'))

    return render_template('HomePage.html', trading_data=trading_data)




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
        flash("Welcome To Cedar Club, Please Login With your account Details")
        return redirect(url_for('home'))
    
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@app.route('/login', methods=['POST'])
def login():
    data = request.form
    LoginData = Login.LoginPage.login(data,User)
    if LoginData == "Wrong Username Or Password":
        flash("Welcome To Cedar Club, Please Login With your account Details")
        return LoginData
    else:
        db.session.add(LoginData)
        db.session.commit()
        login_user(LoginData,remember=True)
        print(current_user.is_authenticated)
        if current_user.is_active :
            return redirect(url_for('HomePage'))
        else:
            flash("Your Subscription has expired Please renew to continue")
            return redirect(url_for('subscribe'))


@app.route('/api/check_session', methods=['GET'])
def check_session():
    if User.is_authenticated:
        return jsonify({'status': 'authenticated'}), 200
    else:
        return jsonify({'status': 'unauthenticated'}), 401


@app.route('/subscribe')
@login_required
def subscribe():
    return render_template('subscribe.html')


@app.route('/pay', methods=['POST'])
def pay():
    # Payment data
    payment_data = {
        "amount": 99900,  # Amount in smallest currency unit e.g. paise for INR
        "currency": "INR",
        "receipt": "order_rcptid_11",
        "notes": {
            "note_key_1": "Tea, Earl Grey, Hot",
            "note_key_2": "Make it so."
        }
    }

    # Create order
    order = client.order.create(data=payment_data)
    if not order:
        return jsonify({'error': 'Cannot create order'}), 500

    return jsonify(order)

@app.route('/success')
def payment_success():
    try:
        current_user.subscription_end_date = datetime.now() + timedelta(days=30)
        db.session.commit()  # Make sure to commit changes
        flash('Payment successful! Subscription is updated.', 'success')
        return redirect(url_for('HomePage'))
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while updating your subscription: {str(e)}', 'error')
        return redirect(url_for('subscribe'))


@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    data = request.get_json()
    verified = client.utility.verify_payment_signature(data)
    if verified:
        user_id = data['user_id']
        user = User.query.get(user_id)
        if user:
            user.subscription_end_date = datetime.now() + timedelta(days=30)
            db.session.add(user)  # This might be redundant if the user is already tracked
            db.session.commit()
            flash('Payment verified successfully! Subscription is updated.', 'success')
            return jsonify({'success': True, 'message': 'Payment verified successfully'})
        else:
            return jsonify({'error': 'User not found'}), 404
    else:
        flash('Payment verification failed.', 'error')
        return jsonify({'success': False, 'message': 'Payment verification failed'}), 400



@app.route('/api/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200


@app.route('/api/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    results = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_active': user.is_active,
        'subscription_end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None
    } for user in users]
    return jsonify(results), 200




@app.route('/api/stock/<int:id>', methods=['DELETE'])
def delete_stock(id):
    stock = TradingSignal.query.get_or_404(id)
    db.session.delete(stock)
    db.session.commit()
    return jsonify({'message': 'Stock deleted successfully'}), 200


@app.route('/api/stock', methods=['DELETE'])
def delete_all_stocks():
    try:
        # Fetch all trading signals from the database
        all_stocks = TradingSignal.query.all()
        
        # Check if there are any trading signals to delete
        if not all_stocks:
            return jsonify({'message': 'No stocks to delete'}), 404
        
        # Delete all trading signals
        for stock in all_stocks:
            db.session.delete(stock)
        
        # Commit the changes to the database
        db.session.commit()
        
        return jsonify({'message': 'All stocks deleted successfully'}), 200
    except Exception as e:
        # Handle exceptions and return an error message
        return jsonify({'error': 'Failed to delete stocks', 'message': str(e)}), 500



@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/pricing')
def pricing():
    return render_template('subscribe.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/refund')
def refund():
    return render_template('refund.html')


if __name__ == '__main__':

    app.run(host='0.0.0.0', port=8000, debug=True)
