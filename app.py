from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_from_directory
import smtplib
import random
import os
from os import environ
import importlib
import threading
import requests
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management

# File to store user credentials
USER_FILE = 'users.txt'

# Automatically register all blueprints from the 'blueprints' folder
def register_blueprints(app):
    blueprints_dir = os.path.join(os.path.dirname(__file__), 'blueprints')

    for filename in os.listdir(blueprints_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = f"blueprints.{filename[:-3]}"
            module = importlib.import_module(module_name)
            blueprint = getattr(module, f"{filename[:-3]}_blueprint")
            app.register_blueprint(blueprint)

register_blueprints(app)

# Serve JavaScript files from 'scripts' folder
@app.route('/scripts/<path:filename>')
def serve_scripts(filename):
    return send_from_directory('scripts', filename)

# Serve static files (CSS, images, etc.) from 'static' folder
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Custom 404 Error Handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Keep-Alive route
@app.route('/keep_alive')
def keep_alive():
    return "I'm alive!", 200

# Function to periodically ping the Keep-Alive route
def keep_alive_task():
    while True:
        try:
            # Send a GET request to the keep_alive route
            requests.get('https://nekotools.onrender.com/keep_alive')
            print("Keep-alive ping sent.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send keep-alive ping: {e}")
        
        # Sleep for 20 minutes (1200 seconds)
        time.sleep(600)

# Helper function to check if the user is logged in
def is_logged_in():
    return 'logged_in' in session

# Helper function to read user data
def read_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as f:
        users = f.readlines()
    user_data = {}
    for user in users:
        email, password, verified = user.strip().split(',')
        user_data[email] = {'password': password, 'verified': verified == 'true'}
    return user_data

# Helper function to check if email is already registered but not verified
def is_email_registered(email):
    users = read_users()
    if email in users and not users[email]['verified']:
        return True
    return False

# Redirect to login page if not logged in
@app.before_request
def require_login():
    allowed_routes = ['login', 'login_user', 'signup', 'send_code_get', 'verify_get', 'verify_code_get', 'congratulations', 'resend_code']
    if not is_logged_in() and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

# Route to serve the login page
@app.route('/')
@app.route('/login')
def login():
    if is_logged_in():
        return redirect(url_for('home'))
    return render_template('login.html')

# Route to process login
@app.route('/login-user', methods=['GET'])
def login_user():
    email = request.args.get('email')
    password = request.args.get('password')
    
    users = read_users()
    if email in users and users[email]['password'] == password and users[email]['verified']:
        session['logged_in'] = True
        return redirect(url_for('home'))
    else:
        # যদি ইমেইল বা পাসওয়ার্ড ভুল হয় তাহলে error বার্তা সহ পুনরায় login পেজ দেখাবে
        error = 'Invalid credentials or email not verified'
        return render_template('login.html', error=error)

# Route to log out the user
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Route to serve the signup page
@app.route('/signup')
def signup():
    if is_logged_in():
        return redirect(url_for('home'))
    return render_template('signup.html')

# Route to send verification code using GET
@app.route('/send-code', methods=['GET'])
def send_code_get():
    email = request.args.get('email')
    password = request.args.get('password')

    users = read_users()

    if email in users and users[email]['verified']:
        # ইমেইল আগে থেকেই ব্যবহারিত এবং ভেরিফাইড
        error = 'This email is already verified and in use.'
        return render_template('signup.html', error=error)
    elif email in users and not users[email]['verified']:
        pass  # Continue to send verification code again

    # Generate a 6-digit verification code
    verification_code = random.randint(100000, 999999)
    session['email'] = email
    session['password'] = password
    session['verification_code'] = verification_code

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('mahfuzshahariar20@gmail.com', 'frpb hwmw ymym xtrq')

        subject = 'Your Verification Code'
        body = f'Your verification code is: {verification_code}'
        message = f'Subject: {subject}\n\n{body}'

        server.sendmail('your-email@gmail.com', email, message)
        server.quit()

        return redirect(url_for('verify_get'))

    except Exception as e:
        print(e)
        return jsonify({'message': 'Error sending email'}), 500

# Route to resend the verification code
@app.route('/resend-code', methods=['GET'])
def resend_code():
    if 'email' not in session:
        return redirect(url_for('signup'))
    
    email = session['email']

    # Generate a new 6-digit verification code
    verification_code = random.randint(100000, 999999)
    session['verification_code'] = verification_code

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('mahfuzshahariar20@gmail.com', 'frpb hwmw ymym xtrq')

        subject = 'Your New Verification Code'
        body = f'Your new verification code is: {verification_code}'
        message = f'Subject: {subject}\n\n{body}'

        server.sendmail('your-email@gmail.com', email, message)
        server.quit()

        return render_template('verify.html', email=email, message='A new verification code has been sent. Please enter the new code.')

    except Exception as e:
        print(e)
        return jsonify({'message': 'Error resending email'}), 500

# Route to serve the verification page using GET
@app.route('/verify', methods=['GET'])
def verify_get():
    if 'email' not in session:
        return redirect(url_for('signup'))
    email = session['email']
    return render_template('verify.html', email=email)

# Route to verify the code using GET
@app.route('/verify-code', methods=['GET'])
def verify_code_get():
    input_code = request.args.get('code')
    if 'verification_code' in session and int(input_code) == session['verification_code']:
        email = session['email']
        password = session['password']
        with open(USER_FILE, 'a') as f:
            f.write(f'{email},{password},true\n')

        session.pop('email', None)
        session.pop('password', None)
        session.pop('verification_code', None)

        session['logged_in'] = True
        return redirect(url_for('home'))
    else:
        return render_template('verify.html', email=session['email'], error='Incorrect verification code. Please try again.')

# Route to show congratulations message
@app.route('/congratulations')
def congratulations():
    if is_logged_in():
        return redirect(url_for('home'))
    return "Congratulations! Your account has been created."

# Home page after successful login
@app.route('/home')
def home():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('home.html')

# Run the app
if __name__ == "__main__":
    threading.Thread(target=keep_alive_task, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
