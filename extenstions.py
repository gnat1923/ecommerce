from flask_login import LoginManager, current_user, login_user

# Initialize Flask-Login
login = LoginManager()
login.login_view = 'login'  # Set the login view