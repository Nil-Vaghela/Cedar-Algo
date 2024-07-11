from urllib.parse import urljoin, urlparse
from flask import Flask, abort, flash, redirect, render_template, request, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from flask_migrate import Migrate
import pytz
import razorpay
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from loginSignup import Login
from TradingSignals import tradingsignals
from SubscriberModel import Subscription



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Nill!6992@cedartrading.chyem684wzw8.us-east-1.rds.amazonaws.com:5432/cedartrading'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PREFERRED_URL_SCHEME'] = 'https'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'loginreq'




client = razorpay.Client(auth=("rzp_test_2hY8PR8G5rKybf", "E8w1YuPcAesivzTuSY5Y87qF"))


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
    password_hash = db.Column(db.String(512))
    subscription_end_date = db.Column(db.DateTime, default=None) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_authenticated(self):
        return True
    
    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return str(self.id)
    
    @property
    def is_active(self):
        """Check if the user's subscription is active."""
        return self.subscription_end_date and self.subscription_end_date > datetime.now()

    def __repr__(self):
        return f'<User {self.username}>'


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
        return redirect(url_for('HomePage'))
    
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@app.route('/loginreq', methods=['POST'])
def loginreq():
    data = request.form
    user = User.query.filter_by(email=data['email']).first()

    if user and user.check_password(data['password']):
        login_user(user, remember=True)

        if user.is_active:
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('HomePage')
            return redirect(next_page)
        else:
            flash('Your subscription has expired. Please renew to continue.', 'warning')
            return redirect(url_for('subscribe'))
    else:
        flash('Invalid username or password.', 'error')
        return redirect(url_for('loginreq'))




@app.route('/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    # if request.method == 'POST':
    #     plan_id = request.form['plan_id']
    #     amount = int(request.form['amount'])  # Convert amount to integer

    #     order = Subscription.PaymentModel.handle_payment(amount)
    #     if 'id' in order:
    #         if Subscription.PaymentModel.verify_payment(order['id'], 'simulated_payment_id', 'simulated_signature'):
    #             # Update the user's subscription details here
    #             print('Subscription updated successfully!', 'success')
    #             return redirect(url_for('HomePage'))
    #         else:
    #             print('Payment verification failed.', 'error')
    #     else:
    #         print(f'Failed to initiate payment: {order}', 'error')
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
@login_required
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
