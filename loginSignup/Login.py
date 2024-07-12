

import requests


class LoginPage():


    def login(request):
        loginUrl = "http://www.cedaralgo.in/api/login"
        email = request['email']
        password = request['password']
        userdata = {
            "email": email,
            "password": password
            }
        
        signup_response = requests.post(loginUrl, json=userdata)
        return signup_response


    def signup(request):
        signup_url = "http://www.cedaralgo.in/api/signup"

        FirstName = request['first_name']
        LastName = request["last_name"]
        email = request['email']
        password = request['password']
        userdata = {
            "first_name": FirstName,
            "last_name": LastName,
            "email": email,
            "password": password
            }
        
        signup_response = requests.post(signup_url, json=userdata)
        return signup_response
        
        # us = User
        # user = us.query.filter_by(email=email).first()
        
        # if user:
        #     return "Email address already exists"
        
        # new_user = User(username=username, email=email)
        # new_user.set_password(password)
        
        # return new_user