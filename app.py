from flask import Flask, render_template, redirect, url_for, jsonify, send_from_directory
import os
import importlib
import requests
import threading
import time
app = Flask(__name__)

# File to store user credentials (Removed)

# Email settings (Removed)

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

# Start the keep-alive thread when the Flask app starts
if __name__ == "__main__":
    threading.Thread(target=keep_alive_task, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
