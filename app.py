from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

def grab(url):
    try:
        response = requests.get(url, timeout=15).text
    except requests.RequestException as e:
        return f"Error fetching URL: {e}"

    if '.m3u8' not in response:
        return 'No .m3u8 link found at the provided URL.'

    end = response.find('.m3u8') + 5
    tuner = 100
    while True:
        if 'https://' in response[end - tuner:end]:
            link = response[end - tuner:end]
            start = link.find('https://')
            end = link.find('.m3u8') + 5
            break
        else:
            tuner += 5
            if tuner > len(response):
                return 'Failed to find .m3u8 link.'

    try:
        streams = requests.get(link[start:end]).text.split('#EXT')
        hd = streams[-1].strip()
        st = hd.find('http')
        if st == -1:
            return 'No stream URL found.'
        else:
            return hd[st:].strip()
    except requests.RequestException as e:
        return f"Error fetching stream URL: {e}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            result = grab(url)
        else:
            result = 'Please provide a URL.'
        return render_template_string('''
            <form method="post">
                <label for="url">Enter URL:</label>
                <input type="text" id="url" name="url" required>
                <button type="submit">Submit</button>
            </form>
            <p>Result:</p>
            <pre>{{ result }}</pre>
        ''', result=result)
    
    return render_template_string('''
        <form method="post">
            <label for="url">Enter URL:</label>
            <input type="text" id="url" name="url" required>
            <button type="submit">Submit</button>
        </form>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
