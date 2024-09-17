from flask import Flask, request, render_template_string
import requests
import re
import logging

app = Flask(__name__)

# লগিং সেটআপ করা
logging.basicConfig(level=logging.DEBUG)

def extract_m3u8_links(html_content):
    try:
        # সোর্স কোড থেকে m3u8 লিঙ্ক বের করার প্যাটার্ন
        m3u8_pattern = r'(https?://[^,\'\"\s]+\.m3u8)'
        m3u8_links = re.findall(m3u8_pattern, html_content)

        if m3u8_links:
            logging.debug(f"M3U8 links extracted: {m3u8_links}")
        else:
            logging.error(f"No M3U8 links found in the page")
        
        return m3u8_links if m3u8_links else []
    except Exception as e:
        logging.error(f"Error in extract_m3u8_links: {str(e)}")
        return []

def extract_partial_source(html_content, marker):
    # নির্দিষ্ট মার্কারের লাইনটি খুঁজে বের করা এবং তার পরবর্তী অংশ নেওয়া
    try:
        index = html_content.find(marker)
        if index != -1:
            logging.debug(f"Marker found at position: {index}")
            # মার্কারের পরে সবকিছু দেখানো হবে
            return html_content[index:]
        else:
            logging.error(f"Marker '{marker}' not found in the source code.")
            return None
    except Exception as e:
        logging.error(f"Error in extract_partial_source: {str(e)}")
        return None

@app.route('/extract', methods=['GET'])
def extract():
    try:
        # ইউজারের ইনপুট URL এবং মার্কার গ্রহণ করা
        url = request.args.get('url')
        marker = request.args.get('marker', '<script name="www-roboto" nonce=')  # ডিফল্ট মার্কার

        if url:
            logging.debug(f"URL received: {url}")
            
            # URL থেকে পেজের সোর্স কোড ডাউনলোড করা
            response = requests.get(url)
            html_content = response.text

            # সোর্স কোড থেকে নির্দিষ্ট মার্কার খুঁজে তার পরের অংশ বের করা
            partial_source = extract_partial_source(html_content, marker)

            # সোর্স কোড থেকে m3u8 লিঙ্কগুলো বের করা
            m3u8_links = extract_m3u8_links(html_content)

            return render_template_string(TEMPLATE, source_code=partial_source, m3u8_links=m3u8_links, error=None)
        else:
            logging.error("No URL parameter provided")
            return render_template_string(TEMPLATE, source_code=None, m3u8_links=None, error="Please provide a valid URL.")
    except Exception as e:
        logging.error(f"Error in /extract route: {str(e)}")
        return render_template_string(TEMPLATE, source_code=None, m3u8_links=None, error="An error occurred while processing the request.")

@app.route('/')
def home():
    return render_template_string(TEMPLATE, source_code=None, m3u8_links=None, error=None)

# HTML টেমপ্লেট তৈরি করা
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
        
        <label for="marker">Enter the Marker (optional):</label>
        <input type="text" id="marker" name="marker" value="<script name='www-roboto' nonce=">

        <button type="submit">Extract M3U8 Links</button>
    </form>

    {% if source_code %}
        <h2>Partial Page Source Code:</h2>
        <pre>{{ source_code }}</pre>
    {% endif %}

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
