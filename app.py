from flask import Flask, request, render_template_string
import requests
import re
import logging

app = Flask(__name__)

# লগিং সেটআপ করা
logging.basicConfig(level=logging.DEBUG)

def extract_m3u8_links(html_content):
    # সোর্স কোড থেকে m3u8 লিঙ্ক বের করার প্যাটার্ন
    m3u8_pattern = r'(https?://[^,\'\"\s]+\.m3u8)'
    m3u8_links = re.findall(m3u8_pattern, html_content)
    return m3u8_links

def extract_script_start(html_content):
    # খোঁজা হচ্ছে '<script name="www-roboto" nonce=' দিয়ে শুরু হওয়া অংশ
    script_pattern = r'hlsManifestUrl'
    match = re.search(script_pattern, html_content)
    
    if match:
        # যদি মেলে, তখন যেখান থেকে মিলেছে, সেই স্থান থেকে সম্পূর্ণ বাকি সোর্স ফেরত দেবে
        return html_content[match.start():]
    return None

@app.route('/extract', methods=['GET'])
def extract():
    try:
        # ইউজারের ইনপুট URL গ্রহণ করা
        url = request.args.get('url')
        if url:
            logging.debug(f"URL received: {url}")
            
            # URL থেকে পেজের সোর্স কোড ডাউনলোড করা
            response = requests.get(url)
            html_content = response.text

            # '<script name="www-roboto" nonce=' দিয়ে শুরু হওয়া অংশ খোঁজা
            script_start = extract_script_start(html_content)
            if script_start:
                # যদি সেই অংশ পাওয়া যায়, তখন সেই অংশ থেকেই m3u8 লিঙ্কগুলো খোঁজা
                m3u8_links = extract_m3u8_links(script_start)
                
                # যদি m3u8 লিঙ্ক না পাওয়া যায়
                if not m3u8_links:
                    return render_template_string(TEMPLATE, source_code=script_start, m3u8_links=None, error="No M3U8 links found in the provided section.")
                
                # যদি m3u8 লিঙ্ক পাওয়া যায়
                return render_template_string(TEMPLATE, source_code=script_start, m3u8_links=m3u8_links, error=None)
            else:
                # যদি '<script name="www-roboto" nonce=' অংশটি না পাওয়া যায়
                return render_template_string(TEMPLATE, source_code=None, m3u8_links=None, error="The specified script section was not found.")
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
        <button type="submit">Extract M3U8 Links</button>
    </form>

    {% if source_code %}
        <h2>Filtered Source Code (after script tag):</h2>
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
