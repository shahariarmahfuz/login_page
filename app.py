from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_from_directory
import smtplib
import random
import os
from os import environ
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import importlib
import threading
import requests
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# File to store user credentials
USER_FILE = 'users.txt'

# Email settings
EMAIL_ADDRESS = 'nekotoolcontact@gmail.com'
EMAIL_PASSWORD = 'isyj gjmc ilua qnyl'

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
            response = requests.get('https://nekotools.onrender.com/keep_alive')
            if response.status_code == 200:
                print("Keep-alive ping sent successfully.")
            else:
                print(f"Keep-alive ping failed with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send keep-alive ping: {e}")
        
        # Sleep for 5 minutes (300 seconds)
        time.sleep(300)

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
        user_data[email] = {'password': password, 'verified': verified.lower() == 'true'}
    return user_data

# Email template
def create_email_message(subject, body):
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
            body {{
                font-family: 'Montserrat', sans-serif;
                background-color: #f0f8ff;
                color: #333333;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                text-align: center;
            }}
            h1 {{
                color: #ff6347;
                font-size: 28px;
                margin-bottom: 10px;
            }}
            .verification-code {{
                font-size: 26px;
                font-weight: bold;
                color: #32cd32;
                margin: 25px 0;
            }}
            .message {{
                color: #666666;
                margin-bottom: 25px;
                font-size: 16px;
            }}
            .thank-you {{
                color: #333333;
                font-size: 18px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>{subject}</h1>
        <p class="message">{body}</p>
        <p class="thank-you">Thank you for staying with us. We will try our best to provide the highest service.</p>
    </body>
    </html>
    """
    return html

# Helper function to send an email
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = 'Neko Tool 🔥'
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(create_email_message(subject, body), 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
    except Exception as e:
        print(e)

# Redirect to login page if not logged in, storing the next route
@app.before_request
def require_login():
    allowed_routes = ['login', 'login_user', 'signup', 'send_code_get', 'verify_get', 'verify_code_get', 'congratulations', 'resend_code', 'forgot_password', 'send_reset_code', 'verify_reset_code', 'reset_password', 'resend_reset_code', 'keep_alive']
    if not is_logged_in() and request.endpoint not in allowed_routes:
        return redirect(url_for('login', next=request.endpoint))

# Route to serve the login page
@app.route('/')
@app.route('/login')
def login():
    if is_logged_in():
        return redirect(url_for('home'))
    next_route = request.args.get('next')
    return render_template('login.html', next_route=next_route)

# Route to process login
@app.route('/login-user', methods=['GET'])
def login_user():
    email = request.args.get('email')
    password = request.args.get('password')
    next_route = request.args.get('next') or 'home'
    
    users = read_users()
    if email in users and users[email]['password'] == password and users[email]['verified']:
        session['logged_in'] = True
        return redirect(url_for(next_route))
    else:
        error = 'Invalid credentials or email not verified'
        return render_template('login.html', error=error, next_route=next_route)

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
        error = 'This email is already verified and in use.'
        return render_template('signup.html', error=error)
    elif email in users and not users[email]['verified']:
        pass  # Continue to send verification code again

    verification_code = random.randint(100000, 999999)
    session['email'] = email
    session['password'] = password
    session['verification_code'] = verification_code

    subject = 'Email Verification Code'
    body = f'Please use the following code to verify your email address: <div class="verification-code">{verification_code}</div>'
    send_email(email, subject, body)

    return redirect(url_for('verify_get'))

# Route to resend the verification code
@app.route('/resend-code', methods=['GET'])
def resend_code():
    if 'email' not in session:
        return redirect(url_for('signup'))
    
    email = session['email']

    verification_code = random.randint(100000, 999999)
    session['verification_code'] = verification_code

    subject = 'New Email Verification Code'
    body = f'A new verification code has been sent. Please use the following code: <div class="verification-code">{verification_code}</div>'
    send_email(email, subject, body)

    return render_template('verify.html', email=email, message='A new verification code has been sent. Please enter the new code.')

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

# Route to serve the forgot password page
@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

# Route to send reset code
@app.route('/send-reset-code', methods=['GET'])
def send_reset_code():
    email = request.args.get('email')
    users = read_users()

    if email not in users or not users[email]['verified']:
        return render_template('forgot_password.html', error='Email not found or not verified.')

    verification_code = random.randint(100000, 999999)
    session['reset_email'] = email
    session['reset_code'] = verification_code

    subject = 'Password Reset Code'
    body = f'Please use the following code to reset your password: <div class="verification-code">{verification_code}</div>'
    send_email(email, subject, body)
    
    return redirect(url_for('verify_reset_code'))

# Route to serve the reset code verification page
@app.route('/verify-reset-code')
def verify_reset_code():
    if 'reset_email' not in session:
        return redirect(url_for('forgot_password'))
    return render_template('verify_reset_code.html', email=session['reset_email'])

# Route to reset the password
@app.route('/reset-password', methods=['GET'])
def reset_password():
    input_code = request.args.get('code')
    new_password = request.args.get('new_password')
    
    if 'reset_code' in session and int(input_code) == session['reset_code']:
        email = session['reset_email']
        users = read_users()
        
        if email in users:
            # Update only the password for the specific email
            users[email]['password'] = new_password
            
            # Re-write the users.txt file, but only change the password for the relevant email
            with open(USER_FILE, 'w') as f:
                for user_email, data in users.items():
                    verified_status = 'true' if data['verified'] else 'false'
                    f.write(f'{user_email},{data["password"]},{verified_status}\n')
            
            # Clear session data after reset
            session.pop('reset_email', None)
            session.pop('reset_code', None)
            
            return redirect(url_for('login'))
        else:
            return render_template('verify_reset_code.html', email=email, error='Email not found.')
    else:
        return render_template('verify_reset_code.html', email=session['reset_email'], error='Incorrect verification code.')

# Route to resend reset code
@app.route('/resend-reset-code')
def resend_reset_code():
    if 'reset_email' not in session:
        return redirect(url_for('forgot_password'))

    email = session['reset_email']
    verification_code = random.randint(100000, 999999)
    session['reset_code'] = verification_code

    subject = 'New Password Reset Code'
    body = f'A new password reset code has been sent. Please use the following code: <div class="verification-code">{verification_code}</div>'
    send_email(email, subject, body)

    return render_template('verify_reset_code.html', email=email, message='A new verification code has been sent.')

# Start the keep-alive thread when the Flask app starts
if __name__ == "__main__":
    threading.Thread(target=keep_alive_task, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
