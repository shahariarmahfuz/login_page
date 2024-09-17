from flask import Flask, request, render_template_string
import requests
import re
import logging

app = Flask(__name__)

# Logging setup
logging.basicConfig(level=logging.DEBUG)

def extract_m3u8_links_near_hls_manifest(html_content):
    # First, locate the 'hlsManifestUrl' part in the HTML content
    hls_manifest_pattern = r'"hlsManifestUrl":"(https?://[^,\'\"\s]+\.m3u8)"'
    match = re.search(hls_manifest_pattern, html_content)
    
    if match:
        # If found, return the matched m3u8 link
        return [match.group(1)]
    return None

@app.route('/extract', methods=['GET'])
def extract():
    try:
        # Get the URL parameter from the request
        url = request.args.get('url')
        if url:
            logging.debug(f"URL received: {url}")
            
            # Fetch the page content from the URL
            response = requests.get(url)
            html_content = response.text

            # Find the m3u8 link near the 'hlsManifestUrl' part
            m3u8_links = extract_m3u8_links_near_hls_manifest(html_content)
            
            if m3u8_links:
                return render_template_string(TEMPLATE, m3u8_links=m3u8_links, error=None)
            else:
                return render_template_string(TEMPLATE, m3u8_links=None, error="No M3U8 links found.")
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
