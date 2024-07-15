import threading
from flask import Flask, jsonify, request
import logging
import socket
import time
import uuid

import requests
from Angleone import BuyStock

app = Flask(__name__)

def fetch_signals(api_url):
    """ Fetch signals from the API and handle errors. """
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching signals: {e}")
        return []

def place_order_for_all_qualified_users(client_local_ip, client_public_ip, mac_address, trading_info):
    users = fetch_signals("http://localhost:5000/api/users/nil123")
    for user in users:
        # Assuming each user has their own set of API credentials and parameters
        BuyStock.BuyStockParams.place_banknifty_order(
            user['api_key'], user['auth_token'], client_local_ip, client_public_ip, mac_address,
            trading_info['tradingsymbol'], trading_info['quantity'], trading_info['tradingtoken'],
            trading_info['stop_loss'], trading_info['trailing_stop_loss'], trading_info['target'], trading_info['buy_price']
        )

def get_ip_info():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    local_ip, public_ip = '127.0.0.1', requests.get('https://api.ipify.org').text
    try:
        s.connect(('10.254.254.254', 1))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    return local_ip, public_ip, ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 2)][::-1])

def run_background_task():
    client_local_ip, client_public_ip, mac_address = get_ip_info()
    monitor_signals(client_local_ip, client_public_ip, mac_address)

def monitor_signals(client_local_ip, client_public_ip, mac_address, interval=3):
    """Monitor the API for new trading signals and handle duplicates."""
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
                    trading_info = {
                        'tradingsymbol': new_signals[0]["name"],
                        'index': new_signals[0]["indexName"],
                        'tradingtoken': new_signals[0]["IndexToken"],
                        'stop_loss': new_signals[0]["sl"],
                        'target': new_signals[0]["target"],
                        'trailing_stop_loss': new_signals[0]["sl"],
                        'buy_price': new_signals[0]["buy"]
                    }

                    if trading_info['index'] == "NIFTY":
                        trading_info['quantity'] = 25
                    elif trading_info['index'] == "FINNIFTY":
                        trading_info['quantity'] = 40
                    elif trading_info['index'] == "BANKNIFTY":
                        trading_info['quantity'] = 15

                    # Place order for all qualified users
                    place_order_for_all_qualified_users(client_local_ip, client_public_ip, mac_address, trading_info)
            else:
                print("Checked API, but no new unique signals were found.")
        else:
            print("No signals received from API in this check.")
        time.sleep(interval)

if __name__ == '__main__':
    thread = threading.Thread(target=run_background_task)
    thread.start()
    app.run(debug=True)
