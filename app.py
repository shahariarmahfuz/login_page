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
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        # Regular expression to find M3U8 links
        links = re.findall(r'(https?://[^\s"]+\.m3u8)', content)
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
    app.run(debug=True)
