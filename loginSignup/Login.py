

class LoginPage():


    def login(request,User):
        email = request.form['email']
        password = request.form['password']
        us = User
        user = us.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            return user
        
        else: 
            return "Wrong Username Or Password"


    def signup(request,User):
        username = request['first_name']
        email = request['email']
        password = request['password']
        us = User
        user = us.query.filter_by(email=email).first()
        
        if user:
            
            return "Email address already exists"
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        return new_user