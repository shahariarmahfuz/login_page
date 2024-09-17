from flask import Flask, request, redirect, render_template_string, jsonify, Response
import requests
import time
import threading
import re
import logging
from urllib.parse import quote

app = Flask(__name__)

M3U_FILE_PATH = 'you.m3u'

def read_m3u_file():
    with open(M3U_FILE_PATH, 'r') as file:
        return file.readlines()

def write_m3u_file(lines):
    with open(M3U_FILE_PATH, 'w') as file:
        file.writelines(lines)

@app.route('/you.m3u', methods=['GET'])
def serve_m3u():
    content = ''.join(read_m3u_file())
    return Response(content, mimetype='text/plain')

@app.route('/use', methods=['GET'])
def update_link():
    channel_name = request.args.get('channel')
    new_link = request.args.get('link')

    if not channel_name or not new_link:
        return jsonify({'error': 'Missing parameters'}), 400

    lines = read_m3u_file()
    updated = False

    for i, line in enumerate(lines):
        if line.startswith('#EXTINF') and channel_name in line:
            # Skip the `#EXTINF` line and replace the next line with the new link
            if i + 1 < len(lines):
                lines[i + 1] = new_link + '\n'
                updated = True
                break

    if updated:
        write_m3u_file(lines)
        return jsonify({'message': 'Link updated successfully'})
    else:
        return jsonify({'error': 'Channel not found'}), 404

def get_live_stream_url(channel_id):
    try:
        # YouTube channel's live page URL
        channel_url = f'https://www.youtube.com/channel/{channel_id}/live'
        response = requests.get(channel_url)
        html_content = response.text

        # Extract live video link
        live_video_pattern = r'https://www\.youtube\.com/watch\?v=[\w-]+'
        video_urls = re.findall(live_video_pattern, html_content)

        if video_urls:
            # Try to get M3U8 link from the first live video
            video_url = video_urls[0]
            m3u8_url = get_m3u8_url(video_url)
            return m3u8_url
        else:
            return None
    except Exception as e:
        logging.error(f"Error getting live stream URL: {e}")
        return None

def get_m3u8_url(video_url):
    try:
        # Extract M3U8 link from video page source
        response = requests.get(video_url)
        html_content = response.text
        m3u8_pattern = r'https://manifest\.googlevideo\.com/api/manifest/hls_variant/expire.*?/file/index\.m3u8'
        m3u8_links = re.findall(m3u8_pattern, html_content)
        return m3u8_links[0] if m3u8_links else None
    except Exception as e:
        logging.error(f"Error getting M3U8 URL: {e}")
        return None

@app.route('/youtube', methods=['GET'])
def youtube():
    # Extract channel ID from URL parameter
    url_id = request.args.get('id')
    if url_id and url_id.endswith('.m3u8'):
        channel_id = url_id.replace('.m3u8', '')
        m3u8_url = get_live_stream_url(channel_id)

        if m3u8_url:
            return redirect(m3u8_url)
        else:
            return render_template_string('''
                <h1>No live stream or M3U8 link found for the provided channel ID.</h1>
                <a href="/">Go Back</a>
            ''')
    else:
        return render_template_string('''
            <h1>Invalid format. Make sure the URL ends with .m3u8 and includes a valid channel ID.</h1>
            <a href="/">Go Back</a>
        ''')

@app.route('/get_code', methods=['GET'])
def get_code():
    link = request.args.get('link')
    if link:
        try:
            response = requests.get(link)
            source_code = response.text

            # Find YouTube channel links
            youtube_channel_pattern = r'https://www\.youtube\.com/channel/([\w-]+)'
            youtube_links = re.findall(youtube_channel_pattern, source_code)
            
            # Remove duplicates
            unique_links = list(set(youtube_links))
            
            # Return results in JSON format
            return jsonify({
                'youtube_channel_ids': unique_links
            })
        except Exception as e:
            logging.error(f"Error fetching the source code: {e}")
            return jsonify({
                'error': 'Error fetching the source code.'
            }), 500
    else:
        return jsonify({
            'error': 'Please provide a valid link.'
        }), 400

# List of channel IDs and names
channels = [
    "ISLAM BANGLA&UCN6sm8iHiPd0cnoUardDAnw",
    "Bangla TV&288uue2737",
    "Nd TV&828jej263"
]

# Request status list
request_status = []

def send_request(channel_name, channel_id):
    base_url_youtube = "https://dc641bf7-026f-48d9-9921-7c77ad2ee137-00-3ijnparc2238r.sisko.replit.dev/youtube?live&id="
    base_url_use = "https://dc641bf7-026f-48d9-9921-7c77ad2ee137-00-3ijnparc2238r.sisko.replit.dev/use?channel="

    # Properly encode parameters
    encoded_channel_name = quote(channel_name)
    youtube_link = f"{base_url_youtube}{channel_id}.m3u8"
    logging.info(f"Requesting YouTube link: {youtube_link}")
    response = requests.get(youtube_link)

    if response.status_code == 200:
        redirected_link = response.url  # Get the redirected link

        # Properly encode parameters
        use_link = f"{base_url_use}{encoded_channel_name}&link={quote(redirected_link)}"
        logging.info(f"Requesting use link: {use_link}")
        use_response = requests.get(use_link)

        if use_response.status_code == 200:
            request_status.append({
                'channel': channel_name,
                'id': channel_id,
                'status': 'Success'
            })
            logging.info(f"Successfully sent link for {channel_name}")
        else:
            request_status.append({
                'channel': channel_name,
                'id': channel_id,
                'status': 'Failed'
            })
            logging.error(f"Failed to send link for {channel_name}, status code: {use_response.status_code}")
    else:
        request_status.append({
            'channel': channel_name,
            'id': channel_id,
            'status': 'Failed'
        })
        logging.error(f"Failed to get redirected link for {channel_name}, status code: {response.status_code}")

# Function to send requests every hour
def background_task():
    while True:
        for channel_info in channels:
            # Split channel name and ID
            channel_name, channel_id = channel_info.split("&")
            send_request(channel_name, channel_id)
        time.sleep(3600)

# Function to clear status every 5 minutes
def clear_status():
    while True:
        time.sleep(300)  # 5 minutes (300 seconds)
        request_status.clear()
        logging.info("Cleared request statuses")

@app.route('/see')
def index():
    # Show request status as JSON
    return jsonify(request_status)

# Start background tasks
if __name__ == "__main__":
    # Background task for sending requests
    threading.Thread(target=background_task).start()

    # Background task for clearing status
    threading.Thread(target=clear_status).start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
