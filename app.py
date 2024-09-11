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

# Email template with updated HTML content
def send_verification_email(to_email, verification_code):
    sender_email = "nekotoolcontact@gmail.com"
    sender_name = "Neko Tool 🔥"
    password = EMAIL_PASSWORD
    subject = "Your Verification Code"

    # Simplified HTML content with thin border and minimal design
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; 
                    padding: 15px; border: 1px solid #007bff;">
            <!-- Header Section -->
            <h2 style="text-align: center; color: white; background-color: #007bff; padding: 10px; 
                       border-radius: 5px; font-size: 20px;">
                {subject}
            </h2>
            
            <!-- Main Body -->
            <p style="color: #333; font-size: 16px; text-align: center;">
                Dear valued user,<br><br>
                Please use the following code to verify your email:
            </p>
            <div style="text-align: center; margin: 20px 0;">
                <h1 style="font-size: 36px; color: #007bff; border: 1px solid #007bff; 
                           display: inline-block; padding: 10px 15px; border-radius: 5px;">
                    {verification_code}
                </h1>
            </div>
            
            <!-- Footer Section -->
            <div style="border-top: 1px solid #ddd; margin-top: 20px; padding-top: 10px; text-align: center;">
                <p style="color: #888; font-size: 12px;">
                    The code is valid for 5 minutes. If you did not request this, please ignore this email.
                </p>
                <p style="color: #666; font-size: 12px; margin-top: 15px;">
                    © Neko Tool 🔥. All Rights Reserved. | 
                    <a href="https://yourwebsite.com/subscription" style="color: #007bff; text-decoration: none;">
                        Manage Subscription
                    </a> | 
                    <a href="https://yourwebsite.com/tutorial" style="color: #007bff; text-decoration: none;">
                        Tutorial
                    </a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    # Setup email content
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    # Send the email using Gmail's SMTP server
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, msg.as_string())
        print(f"Verification code {verification_code} sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

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

    # Send the verification email using the updated template
    send_verification_email(email, verification_code)

    return redirect(url_for('verify_get'))

# Route to resend the verification code
@app.route('/resend-code', methods=['GET'])
def resend_code():
    if 'email' not in session:
        return redirect(url_for('signup'))
    
    email = session['email']

    verification_code = random.randint(100000, 999999)
    session['verification_code'] = verification_code

    # Resend the verification email using the updated template
    send_verification_email(email, session['verification_code'])

    return redirect(url_for('verify_get'))

# Route to serve the verification page
@app.route('/verify')
def verify_get():
    if 'email' not in session:
        return redirect(url_for('signup'))
    return render_template('verify.html')

# Route to verify the code
@app.route('/verify-code', methods=['GET'])
def verify_code_get():
    code = request.args.get('code')
    email = session.get('email')
    password = session.get('password')
    verification_code = session.get('verification_code')

    if not email or not verification_code:
        return redirect(url_for('signup'))

    if str(code) == str(verification_code):
        users = read_users()
        users[email] = {'password': password, 'verified': True}
        with open(USER_FILE, 'w') as f:
            for user, data in users.items():
                f.write(f"{user},{data['password']},{data['verified']}\n")

        session.pop('verification_code', None)
        session['logged_in'] = True
        return redirect(url_for('congratulations'))
    else:
        error = 'Invalid verification code'
        return render_template('verify.html', error=error)

# Route to serve the congratulations page
@app.route('/congratulations')
def congratulations():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('congratulations.html')

# Route to serve the forgot password page
@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

# Route to send reset code
@app.route('/send-reset-code', methods=['GET'])
def send_reset_code():
    email = request.args.get('email')
    users = read_users()

    if email not in users:
        error = 'Email not found'
        return render_template('forgot_password.html', error=error)

    reset_code = random.randint(100000, 999999)
    session['reset_code'] = reset_code
    session['reset_email'] = email

    # Send the reset code via email
    send_verification_email(email, reset_code)

    return redirect(url_for('verify_reset_code'))

# Route to serve the verify reset code page
@app.route('/verify-reset-code')
def verify_reset_code():
    if 'reset_email' not in session:
        return redirect(url_for('forgot_password'))
    return render_template('verify_reset_code.html')

# Route to verify the reset code
@app.route('/verify-reset-code', methods=['GET'])
def verify_reset_code_get():
    code = request.args.get('code')
    reset_code = session.get('reset_code')

    if not reset_code or str(code) != str(reset_code):
        error = 'Invalid reset code'
        return render_template('verify_reset_code.html', error=error)

    session.pop('reset_code', None)
    return redirect(url_for('reset_password'))

# Route to serve the reset password page
@app.route('/reset-password')
def reset_password():
    if 'reset_email' not in session:
        return redirect(url_for('forgot_password'))
    return render_template('reset_password.html')

# Route to handle the reset password process
@app.route('/reset-password', methods=['POST'])
def reset_password_post():
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    email = session.get('reset_email')

    if not email:
        return redirect(url_for('forgot_password'))

    if new_password != confirm_password:
        error = 'Passwords do not match'
        return render_template('reset_password.html', error=error)

    users = read_users()
    if email in users:
        users[email]['password'] = new_password
        with open(USER_FILE, 'w') as f:
            for user, data in users.items():
                f.write(f"{user},{data['password']},{data['verified']}\n")
        
        session.pop('reset_email', None)
        return redirect(url_for('login'))
    else:
        error = 'Email not found'
        return render_template('reset_password.html', error=error)

# Route to resend the reset code
@app.route('/resend-reset-code', methods=['GET'])
def resend_reset_code():
    if 'reset_email' not in session:
        return redirect(url_for('forgot_password'))

    email = session['reset_email']
    reset_code = random.randint(100000, 999999)
    session['reset_code'] = reset_code

    # Resend the reset code via email
    send_verification_email(email, reset_code)

    return redirect(url_for('verify_reset_code'))

# Run the periodic keep-alive task in a separate thread
keep_alive_thread = threading.Thread(target=keep_alive_task)
keep_alive_thread.daemon = True
keep_alive_thread.start()

if __name__ == "__main__":
    threading.Thread(target=keep_alive_task, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
