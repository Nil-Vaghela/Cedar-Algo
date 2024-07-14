import json
from SmartApi import SmartConnect
import requests


class BuyStockParams():
    def place_banknifty_order(api_key, auth_token, client_local_ip, client_public_ip, mac_address, tradingsymbol, quantity, tradingtoken, stop_loss, trailing_stop_loss,target):
        url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/order/v1/placeOrder"
        headers = {
            'Authorization': auth_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': client_local_ip,
            'X-ClientPublicIP': client_public_ip,
            'X-MACAddress': mac_address,
            'X-PrivateKey': api_key
        }
        payload = {
            "variety": "ROBO",
            "tradingsymbol": tradingsymbol,
            "symboltoken": tradingtoken,  # Update with the actual symbol token for Banknifty
            "transactiontype": "BUY",
            "exchange": "NFO",
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "quantity": quantity,
            "stoploss": stop_loss,
            "squareoff": target,
            "trailingStopLoss": trailing_stop_loss,
            "triggerprice":str( int(stop_loss) + 1)
        }


        response = requests.post(url, headers=headers, data=json.dumps(payload))
        # smartApi = SmartConnect(api_key)
        # response = smartApi.placeOrder(payload)
        if response.status_code == 200:
            print("Order placed successfully!")
            print("Response:", response.json())
        else:
            print("Failed to place order")
            print("Status Code:", response.status_code)
            print("Response:", response.json())