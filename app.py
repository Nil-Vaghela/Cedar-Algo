import logging
import os
from datetime import datetime, timedelta
import re
import socket
import threading
import time
from urllib.parse import urljoin, urlparse
import uuid
from flask import Flask, jsonify, render_template, request, redirect, session, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

import requests
from werkzeug.security import generate_password_hash, check_password_hash
import razorpay
from Angleone import BrokerLogin, BuyStock
from loginSignup import Login
from celery import Celery
from redis import Redis

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Nill!6992@cedartrading.chyem684wzw8.us-east-1.rds.amazonaws.com:5432/cedartrading'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "Nill6992"

#Celery
app.config['CELERY_BROKER_URL'] = 'redis://www.cedaralgo.in:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://www.cedaralgo.in:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


db = SQLAlchemy(app)
migrate = Migrate(app, db)

@app.before_request
def make_session_permanent():
    session.permanent = True


login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

client = razorpay.Client(auth=("rzp_live_8kQ21NWsMXOu2S", "Q6rWc0EoKLmODmLKzAvKvz2S")) # live
#client = razorpay.Client(auth=("rzp_test_2hY8PR8G5rKybf", "E8w1YuPcAesivzTuSY5Y87qF")) #test

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))
    api_key = db.Column(db.String(512))  # Stores API key
    Api_Username = db.Column(db.String(512))  # Stores API secret
    pin = db.Column(db.String(100))  # Stores PIN for additional security
    totp_secret = db.Column(db.String(512))  # Stores TOTP secret for two-factor authentication
    subscription_end_date = db.Column(db.DateTime, nullable=True)
    auth_token = db.Column(db.String(2048))  # Stores the authorization token
    refresh_token = db.Column(db.String(2048))  # Stores the refresh token
    feed_token = db.Column(db.String(2048))
    credit = db.Column(db.Integer, default=0)
    referred_by = db.Column(db.String(80), nullable=True)

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
        return True
    @property
    def is_anonymous(self):
        """Always return False, as anonymous users aren't supported."""
        return False

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return str(self.id)
    
    def get_referred_by(self):
        return self.referred_by

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


@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')
    referrer = data.get('referrer', None)

    if not first_name or not last_name or not email or not password:
        return jsonify({'error': 'Missing fields'}), 400

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already in use'}), 409

    # Create username from first name and last_id
    last_id = db.session.query(db.func.max(User.id)).scalar()
    username = f"{first_name}{last_id + 1 if last_id else 1}"

    new_user = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        referred_by=referrer,
        subscription_end_date=datetime.now() + timedelta(days=1)
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully', 'user_id': new_user.id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Both email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):

        login_user(user, remember=True)
        user_info = {
            'user_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'email': user.email,
            'subscription_end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None
        }
        return jsonify({'message': 'Login successful', 'user': user_info}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401



@app.route('/signupreq', methods=['POST'])
def signupreq():
    data = request.form
    signup = Login.LoginPage.signup(data)
    if signup.status_code == 201:
        # Extract user ID from signup response
        user_id = signup.json().get('user_id')
        
        # Fetch user from database
        user = User.query.get(user_id)
        if user:
            login_user(user, remember=True)  # Log in the user
            session['user_id'] = user_id  # Optionally store the user ID in the session
            user.referred_by = data.get('referrer',)
            # Set the subscription end date to two days from now
            user.subscription_end_date = datetime.now() + timedelta(days=2)
            db.session.commit()  # Commit the update to the database

            flash("Welcome to Cedar Club, your account has been created with a 2-day free trial.")
            return redirect(url_for('HomePage'))  # Redirect to homepage
        else:
            flash("User registration successful, but an error occurred. Please try logging in.")
            return redirect(url_for('home'))
    else:
        # If signup was not successful, show an error message and redirect
        flash("Signup failed. Please try again.")
        return redirect(url_for('home'))

@app.route('/loginreq', methods=['POST'])
def loginreq():
    data = request.form
    login_response = Login.LoginPage.login(data,)
    if login_response.status_code == 200:
        user_info = login_response.json()
        session['user_info'] = user_info['user']  # Storing user info in session
        userdata = user_info['user'] 

        user = User.query.filter_by(email=userdata['email']).first()
        test  = login_user(user, remember=True)
        print(test)
        # Check if the subscription has expired
        if userdata['subscription_end_date'] is None:
            return redirect(url_for('subscribe'))
        else:
            # Assuming subscription_end_date is stored in ISO 8601 format as a string
            if isinstance(userdata['subscription_end_date'], str):
                subscription_end_date = datetime.strptime(userdata['subscription_end_date'], "%Y-%m-%dT%H:%M:%S.%f")
            else:
                subscription_end_date = userdata['subscription_end_date']
            
            # Check if the subscription has expired
            if subscription_end_date > datetime.now():
                return redirect(url_for('HomePage'))
            else:
                return redirect(url_for('subscribe'))
        

    else:
        return jsonify(login_response.json()), login_response.status_code

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


@app.route('/api/user/<int:user_id>/add_credit', methods=['POST'])
def add_credit(user_id):
    # Retrieve the user from the database
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get the credit amount from the request data
    data = request.get_json()
    credit_to_add = data.get('credit')
    
    if credit_to_add is None:
        return jsonify({'error': 'No credit amount provided'}), 400

    try:
        # Convert credit to integer and add it to the user's current credit
        credit_to_add = int(credit_to_add)
        if user.credit is None:
            user.credit = 0
        user.credit += credit_to_add
        db.session.commit()
        return jsonify({'message': 'Credit added successfully', 'total_credit': user.credit}), 200
    except ValueError:
        return jsonify({'error': 'Invalid credit amount'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add credit', 'message': str(e)}), 500
    

def add_credit_to_user(user_id, credit_amount):
    """
    Function to add credit to a user's account via the API.

    Args:
    - user_id (int): The ID of the user to whom credit will be added.
    - credit_amount (int): The amount of credit to add.
    - api_url (str): The base URL of the API.

    Returns:
    - response (dict): The JSON response from the API which includes status message or error.
    """
    # Construct the full API endpoint URL
    endpoint = f"http://127.0.0.1:8000/api/user/{user_id}/add_credit"
    
    # Prepare the data payload as a JSON
    payload = {'credit': credit_amount}

    try:
        # Send a POST request to the API
        response = requests.post(endpoint, json=payload)
        # Return the JSON response
        return response.json()
    except requests.RequestException as e:
        # Handle any errors that occur during the request
        return {'error': 'Request failed', 'message': str(e)}


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

    # if not User.is_active:
    #     print('Your subscription has expired. Please renew.', 'warning')
    #     return redirect(url_for('subscribe'))
    days_left = None
    if current_user.subscription_end_date:
        days_left = (current_user.subscription_end_date - datetime.now()).days


    return render_template('HomePage.html', trading_data=trading_data,days_left=days_left)


@app.route('/api/check_session', methods=['GET'])
def check_session():
    if current_user.is_authenticated:
        return jsonify({'status': 'authenticated'}), 200
    else:
        return jsonify({'status': 'unauthenticated'}), 401


@app.route('/subscribe', methods=['GET'])
@login_required
def subscribe():
    return render_template('subscribe.html')


CreditAmount = 0

@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()  # Get data from JSON payload
    amount = data.get('amount')  # Access the amount sent from the client
    global CreditAmount
    CreditAmount = 0
    CreditAmount = amount
    payment_data = {
        "amount": amount,  # Use the amount from the client
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

    subEndDate = datetime.now() + timedelta(days=30)
    ref = current_user.get_referred_by()

    try:
        if current_user.get_referred_by() == "":
            if CreditAmount == 299900:
                subEndDate = datetime.now() + timedelta(days=30)
                
            elif CreditAmount == 1299900:
                subEndDate = datetime.now() + timedelta(days=180)
            elif CreditAmount == 1999900:
                subEndDate = datetime.now() + timedelta(days=365)
        else :
            referrer = current_user.get_referred_by()
            digits = re.findall(r'\d+', referrer)
            referrer_id = int(''.join(digits))
            if CreditAmount == 299900:
                subEndDate = datetime.now() + timedelta(days=30)
                add_credit_to_user(referrer_id,399)
            elif CreditAmount == 1299900:
                subEndDate = datetime.now() + timedelta(days=180)
                add_credit_to_user(referrer_id,699)
            elif CreditAmount == 1999900:
                subEndDate = datetime.now() + timedelta(days=365)
                add_credit_to_user(referrer_id,999)

        current_user.subscription_end_date = subEndDate
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
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'email': user.email,
        'api_key': user.api_key,  # Assuming you want to expose the API key
        'Api_Username': user.Api_Username,  # Never expose API secrets
        'pin': user.pin,  # Assuming the PIN should also be secured
        'totp_secret': user.totp_secret,  # Never expose TOTP secrets
        'subscription_end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None,
        'credit': user.credit,  # Exposing the credit amount
        'referred_by': user.referred_by
        
    } for user in users]
    return jsonify(results), 200

@app.route('/profile')
def profile():
    user_id = current_user.get_id()
    user = User.query.get_or_404(user_id)
    return render_template('profilePage.html', user=user)

@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user = User.query.get(user_id)
    if not user:
        abort(404, description="User not found")
    
    user_data = {
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'Api_Username': user.Api_Username,
        'email': user.email,
        'api_key': user.api_key,  # Caution: Sensitive data
        'auth_token': user.auth_token,  # Caution: Sensitive data
        'refresh_token': user.refresh_token,  # Caution: Sensitive data
        'feed_token': user.feed_token,  # Caution: Sensitive data
        'pin': user.pin,  # Assuming the PIN should also be secured
        'totp': user.totp_secret,  # Never expose TOTP secrets
        'subscription_end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None,
        'credit': user.credit,  # Exposing the credit amount
        'referred_by': user.referred_by
    }

    return jsonify(user_data), 200


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

@app.route('/Steps')
def Steps():
    return render_template('StepsToAddAngleOne.html')



def get_ip_info():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    local_ip, public_ip = '127.0.0.1', requests.get('https://api.ipify.org').text
    try:
        s.connect(('10.254.254.254', 1))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    return local_ip, public_ip, ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 2)][::-1])


@app.route('/api/submit_credit', methods=['POST'])
def submit_credit():
    user_id = current_user.get_id()
    user = User.query.get_or_404(user_id)
    if user.credit is None:
        user.credit = 0
    if user.credit > 0:
        # Assume a function to process the withdrawal here

        user.credit = 0  # Reset credits after withdrawal
        db.session.commit()
        flash('Your withdrawal request has been processed successfully!', 'success')
    else:
        flash('Insufficient credits for withdrawal.', 'error')

    return redirect(url_for('profile'))

@app.route('/AlgoSetup', methods=['GET', 'POST'])
def AlgoSetup():

    user_id = current_user.get_id()
    url = f"http://www.cedaralgo.in/api/user/{user_id}"

    response = requests.get(url)
    CredentialUser = response.json()
    
    if request.method == 'POST':
        user = User.query.get(user_id)
        # Update user credentials based on form input
        user.Api_Username = request.form.get('Api_Username')
        user.api_key = request.form.get('api_key')
        user.pin = request.form.get('pin')
        user.totp_secret = request.form.get('totp')
        db.session.commit()


        Api_Username  = request.form.get('Api_Username')
        api_key = request.form.get('api_key')
        pin = request.form.get('pin')
        totp = request.form.get('totp')

        # Assuming LoginSmartConnect returns tokens
        
        auth_token, refresh_token, feed_token = BrokerLogin.Brokerlogin.login_to_smart_api(totp,Api_Username,pin,api_key)
        if all([auth_token, refresh_token, feed_token]):
            user.auth_token = auth_token
            user.refresh_token = refresh_token
            user.feed_token = feed_token
            db.session.commit()
            local_ip, public_ip, mac_address = get_ip_info()
            
            thread = monitor_signals.delay(api_key, auth_token, local_ip, public_ip, mac_address, 3)
        
            flash('Settings Updated Successfully!', 'success')
        else:
            flash('Failed to update settings due to API error', 'error')

        return redirect(url_for('AlgoSetup'))
    
    return render_template('AlgoSetup.html', credentials=CredentialUser)

def store_tokens(user_id, auth_token, refresh_token, feed_token):
    user = User.query.get(user_id)
    if user:
        user.auth_token = auth_token
        user.refresh_token = refresh_token
        user.feed_token = feed_token
        db.session.commit()

def get_tokens(user_id):
    user = User.query.get(user_id)
    if user:
        return user.auth_token, user.refresh_token, user.feed_token
    return None, None, None




logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_signals(api_url):
    """ Fetch signals from the API and handle errors. """
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching signals: {e}")
        return []
    



@celery.task
def monitor_signals(api_key, auth_token, client_local_ip, client_public_ip, mac_address,interval=3,):
    """ Monitor the API for new trading signals and handle duplicates. """
    seen_ids = set()  # Stores the IDs of already seen signals to avoid duplication
    while True:
        signals = fetch_signals('https://www.cedaralgo.in/api/trading_signals')
        
        if signals:
            # Filter out signals that have already been seen
            new_signals = [signal for signal in signals if signal['id'] not in seen_ids]
            if new_signals:
                seen_ids.update(signal['id'] for signal in new_signals)
                logging.info(f"New signals received: {new_signals}")
                if len(new_signals) == 1:
                    tradingsymbol = new_signals[0]["name"]
                    index = new_signals[0]["indexName"]

                    if index == "NIFTY":
                        quantity = 25
                    elif index == "FINNIFTY":
                        quantity = 40
                    elif index == "BANKNIFTY":
                        quantity = 15
                    
                    tradingtoken = new_signals[0]["IndexToken"]
                    stop_loss = new_signals[0]["sl"]
                    target = new_signals[0]["target"]
                    tralingstoploss = new_signals[0]["sl"]
                    BuyPrice = new_signals[0]["buy"]

                    BuyStock.BuyStockParams.place_banknifty_order(
                        api_key, auth_token, client_local_ip, client_public_ip, mac_address, tradingsymbol, quantity, tradingtoken, stop_loss, tralingstoploss,target=target,buy=BuyPrice
                    )
                    
                    #BuyStock.BuyStockParams.place_banknifty_order
            else:
                logging.info("Checked API, but no new unique signals were found.")
        else:
            logging.info("No signals received from API in this check.")
        time.sleep(interval)



        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
