from flask import Flask, request, render_template_string
import requests
import re
import logging

app = Flask(__name__)

# Logging setup
logging.basicConfig(level=logging.DEBUG)

def extract_m3u8_links_from_stream(url):
    m3u8_pattern = re.compile(r'https://manifest\.googlevideo\.com/api/manifest/hls_variant/expire.*?/file/index\.m3u8')
    script_pattern = re.compile(r'<script name="www-roboto" nonce=.*')
    found_script_section = False
    m3u8_links = []

    try:
        # Stream the content
        with requests.get(url, stream=True) as response:
            for chunk in response.iter_content(chunk_size=1024):
                if not found_script_section:
                    # Look for the script section in each chunk
                    script_match = script_pattern.search(chunk.decode('utf-8', errors='ignore'))
                    if script_match:
                        found_script_section = True
                        logging.debug("Found the script section, starting M3U8 extraction.")
                        # Start searching for M3U8 links in the remaining part
                        m3u8_links += m3u8_pattern.findall(chunk.decode('utf-8', errors='ignore'))
                else:
                    # Search for M3U8 links in subsequent chunks
                    m3u8_links += m3u8_pattern.findall(chunk.decode('utf-8', errors='ignore'))

                # Stop once we have enough m3u8 links
                if m3u8_links:
                    break

        return m3u8_links

    except Exception as e:
        logging.error(f"Error while streaming the page: {str(e)}")
        return []

@app.route('/extract', methods=['GET'])
def extract():
    try:
        url = request.args.get('url')
        if url:
            logging.debug(f"URL received: {url}")
            m3u8_links = extract_m3u8_links_from_stream(url)
            if not m3u8_links:
                return render_template_string(TEMPLATE, m3u8_links=None, error="No M3U8 links found in the provided section.")
            return render_template_string(TEMPLATE, m3u8_links=m3u8_links, error=None)
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
