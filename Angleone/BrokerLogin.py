from SmartApi import SmartConnect
import pyotp


class Brokerlogin():
    def login_to_smart_api(totp_key,api_username,pin,api_key):

        smartApi = SmartConnect(api_key)
        totp = pyotp.TOTP(totp_key).now()
        data = smartApi.generateSession(api_username, pin, totp)
        if not data['status']:
            print(f"Error {data}")
            return None
        return data['data']['jwtToken'], data['data']['refreshToken'], data['data']['feedToken']