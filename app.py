from flask import Flask, request, render_template_string
import requests
import re
import logging

app = Flask(__name__)

# লগিং সেটআপ করা
logging.basicConfig(level=logging.DEBUG)

def extract_m3u8_links(url):
    try:
        # ইউজার প্রদত্ত URL থেকে পেজের সোর্স কোড ডাউনলোড করা
        logging.debug(f"Fetching URL: {url}")
        response = requests.get(url)
        html_content = response.text

        # সোর্স কোড থেকে m3u8 লিঙ্ক বের করার প্যাটার্ন
        m3u8_pattern = r'(https?://[^,\'\"\s]+\.m3u8)'
        m3u8_links = re.findall(m3u8_pattern, html_content)

        if m3u8_links:
            logging.debug(f"M3U8 links extracted: {m3u8_links}")
        else:
            logging.error(f"No M3U8 links found in the page: {url}")
        
        return m3u8_links if m3u8_links else None
    except Exception as e:
        logging.error(f"Error in extract_m3u8_links: {str(e)}")
        return None

@app.route('/extract', methods=['POST'])
def extract():
    try:
        # ফর্ম থেকে ইউজারের ইনপুট URL নেয়া
        url = request.form.get('url')
        if url:
            logging.debug(f"URL received: {url}")
            
            # URL থেকে m3u8 লিঙ্কগুলো বের করা
            m3u8_links = extract_m3u8_links(url)

            if m3u8_links:
                return render_template_string(TEMPLATE, m3u8_links=m3u8_links, error=None)
            else:
                logging.error(f"No M3U8 links found for URL: {url}")
                return render_template_string(TEMPLATE, m3u8_links=None, error="No M3U8 links found in the provided URL.")
        else:
            logging.error("No URL parameter provided")
            return render_template_string(TEMPLATE, m3u8_links=None, error="Please provide a valid URL.")
    except Exception as e:
        logging.error(f"Error in /extract route: {str(e)}")
        return render_template_string(TEMPLATE, m3u8_links=None, error="An error occurred while processing the request.")

@app.route('/')
def home():
    return render_template_string(TEMPLATE, m3u8_links=None, error=None)

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
    <form action="/extract" method="POST">
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
