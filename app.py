from flask import Flask, request, render_template_string
import requests
import re
import logging
import os
import threading
import time

app = Flask(__name__)

# Logging setup
logging.basicConfig(level=logging.DEBUG)

UPLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_m3u8_links_from_file(filepath):
    m3u8_pattern = re.compile(r'https://manifest\.googlevideo\.com/api/manifest/hls_variant/expire.*?/file/index\.m3u8')
    m3u8_links = []

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                # Search for M3U8 links in the file line by line
                m3u8_links += m3u8_pattern.findall(line)

        return m3u8_links

    except Exception as e:
        logging.error(f"Error while reading the file: {str(e)}")
        return []

def download_file_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], 'downloaded_file.html')
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(response.text)
            logging.debug(f"File downloaded successfully from {url}")
            return filename
        else:
            logging.error(f"Failed to download file: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error while downloading the file: {str(e)}")
        return None

def delete_file_after_delay(filepath, delay=120):
    """
    Delete the specified file after a delay.
    """
    time.sleep(delay)
    try:
        os.remove(filepath)
        logging.debug(f"Deleted file after delay: {filepath}")
    except Exception as e:
        logging.error(f"Error while deleting the file: {str(e)}")

@app.route('/extract', methods=['GET'])
def extract():
    try:
        url = request.args.get('url')
        if url:
            logging.debug(f"URL received: {url}")
            
            # Download the file from the given URL
            filepath = download_file_from_url(url)
            if filepath:
                # Extract M3U8 links from the downloaded file
                m3u8_links = extract_m3u8_links_from_file(filepath)
                
                # Start a background thread to delete the file after 2 minutes
                threading.Thread(target=delete_file_after_delay, args=(filepath, 120)).start()
                
                if not m3u8_links:
                    return render_template_string(TEMPLATE, m3u8_links=None, error="No M3U8 links found.")
                return render_template_string(TEMPLATE, m3u8_links=m3u8_links, error=None)
            else:
                return render_template_string(TEMPLATE, m3u8_links=None, error="Failed to download the file.")
        else:
            logging.error("No URL parameter provided")
            return render_template_string(TEMPLATE, m3u8_links=None, error="Please provide a valid URL.")
    except Exception as e:
        logging.error(f"Error in /extract route: {str(e)}")
        return render_template_string(TEMPLATE, m3u8_links=None, error="An error occurred while processing the request.")

@app.route('/')
def home():
    return render_template_string(TEMPLATE, m3u8_links=None, error=None)

# HTML template
TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M3U8 Link Extractor</title>
</head>
<body>
    <h1>M3U8 Link Extractor</h1>
    <form action="/extract" method="GET">
        <label for="url">Enter the Website URL:</label>
        <input type="text" id="url" name="url" required>
        <button type="submit">Extract M3U8 Links</button>
    </form>

    {% if m3u8_links %}
        <h2>Found M3U8 Links:</h2>
        <ul>
        {% for link in m3u8_links %}
            <li><a href="{{ link }}" target="_blank">{{ link }}</a></li>
        {% endfor %}
        </ul>
    {% elif error %}
        <h2>Error:</h2>
        <p>{{ error }}</p>
    {% endif %}
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
