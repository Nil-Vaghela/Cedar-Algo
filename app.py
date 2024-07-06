from flask import Flask, abort, flash, redirect, render_template, request, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Nill!6992@cedartrading.chyem684wzw8.us-east-1.rds.amazonaws.com:5432/cedartrading'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
    email = db.Column(db.String(120), unique=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())

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
        'created_at': user.created_at.isoformat()
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
