from flask import Flask, render_template, redirect, url_for, jsonify, send_from_directory
import os
import importlib
import requests
import threading
import time
import re
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
# Multiple M3U URLs
m3u_urls = {
    "Link 1": "https://raw.githubusercontent.com/FunctionError/PiratesTv/main/combined_playlist.m3u",
    "Link 2": "https://1rdk.short.gy/Himel-Op-Premium-Playlist.m3u",
}

# Function to parse the m3u file and extract channel information
def parse_m3u(m3u_url):
    response = requests.get(m3u_url)
    content = response.text

    # Regex to extract channel details and URLs
    pattern = re.compile(r'#EXTINF:-1.*?tvg-logo="(.*?)".*?group-title="(.*?)".*?,(.*?)\n(.*?)\n')
    channels = []
    
    matches = pattern.findall(content)
    for match in matches:
        logo, group_title, channel_name, stream_url = match
        channels.append({
            "name": channel_name,
            "logo": logo,
            "group": group_title,
            "url": stream_url
        })

    return channels

# Home route to show M3U options and default to the first M3U link
@app.route('/')
def index():
    default_link = next(iter(m3u_urls.keys()))
    selected_link = request.args.get('link', default_link)
    
    channels = parse_m3u(m3u_urls[selected_link])
    
    # Group channels by their group-title
    grouped_channels = {}
    for channel in channels:
        group = channel["group"]
        if group not in grouped_channels:
            grouped_channels[group] = []
        grouped_channels[group].append(channel)
    
    return render_template('index.html', m3u_urls=m3u_urls, grouped_channels=grouped_channels, selected_link=selected_link)

# Route to load a specific channel
@app.route('/channel/<link_name>/<channel_name>')
def view_channel(link_name, channel_name):
    m3u_url = m3u_urls.get(link_name)
    if not m3u_url:
        return "Invalid M3U link", 404
    
    channels = parse_m3u(m3u_url)

    # Find the channel details by name
    channel = next((ch for ch in channels if ch['name'] == channel_name), None)

    if channel:
        # Get related channels from the same group
        related_channels = [ch for ch in channels if ch['group'] == channel['group'] and ch['name'] != channel_name]
        # Limit the number of related channels to 5
        related_channels = related_channels[:5]
        return render_template('channel.html', channel=channel, related_channels=related_channels, link_name=link_name)
    else:
        return "Channel not found", 404

# Route to fetch channels for a given M3U link
@app.route('/channels/<link_name>')
def fetch_channels(link_name):
    m3u_url = m3u_urls.get(link_name)
    if not m3u_url:
        return jsonify({'error': 'Invalid M3U link'}), 404

    channels = parse_m3u(m3u_url)
    
    # Group channels by their group-title
    grouped_channels = {}
    for channel in channels:
        group = channel["group"]
        if group not in grouped_channels:
            grouped_channels[group] = []
        grouped_channels[group].append(channel)

    return jsonify({'grouped_channels': [{'group': group, 'channels': channels} for group, channels in grouped_channels.items()]})
# Start the keep-alive thread when the Flask app starts

if __name__ == "__main__":
    threading.Thread(target=keep_alive_task, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
