from flask import Flask, request, render_template_string
import requests
import re

app = Flask(__name__)

# HTML Template for input and results
html_template = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>M3U8 Link Extractor</title>
</head>
<body>
    <h1>M3U8 Link Extractor</h1>
    <form method="get">
        <label for="url">Enter URL:</label>
        <input type="text" id="url" name="url" required>
        <button type="submit">Extract M3U8 Links</button>
    </form>
    {% if links %}
        <h2>Extracted M3U8 Links:</h2>
        <ul>
            {% for link in links %}
                <li><a href="{{ link }}" target="_blank">{{ link }}</a></li>
            {% endfor %}
        </ul>
    {% elif error %}
        <p>{{ error }}</p>
    {% endif %}
</body>
</html>
'''

def extract_m3u8_links(url):
    try:
        # Perform a streaming GET request to handle large content
        response = requests.get(url, stream=True)
        response.raise_for_status()
        links = []
        buffer = ''
        for chunk in response.iter_content(chunk_size=2048):
            buffer += chunk.decode('utf-8', errors='ignore')
            # Search within the buffer for M3U8 links
            links.extend(re.findall(r'(https?://[^\s"]+\.m3u8)', buffer))
            # Reset buffer if it gets too large
            if len(buffer) > 10_000:  # Adjust size as necessary
                buffer = ''
        return links
    except Exception as e:
        return str(e)

@app.route('/', methods=['GET'])
def index():
    url = request.args.get('url')
    links = []
    error = None
    if url:
        links = extract_m3u8_links(url)
        if isinstance(links, str):  # If there's an error message
            error = links
            links = []
    return render_template_string(html_template, links=links, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
