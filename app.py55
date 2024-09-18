from flask import Flask, render_template, request
import os
import requests

app = Flask(__name__)

# Function to grab m3u8 link from YouTube or other sources
def grab_youtube_m3u8(url):
    command = f'yt-dlp -g {url}'
    m3u8_link = os.popen(command).read().strip()
    if m3u8_link:
        return m3u8_link
    else:
        return "No m3u8 link found for this URL."

def grab(url):
    try:
        response = requests.get(url, timeout=15).text
        if '.m3u8' not in response:
            response = requests.get(url).text
        end = response.find('.m3u8') + 5
        tuner = 100
        while True:
            if 'https://' in response[end-tuner:end]:
                link = response[end-tuner:end]
                start = link.find('https://')
                end = link.find('.m3u8') + 5
                return link[start:end]
            else:
                tuner += 5
    except Exception as e:
        return f"Error: {e}"

@app.route('/', methods=['GET', 'POST'])
def index():
    m3u8_link = None
    if request.method == 'POST':
        url = request.form['url']
        if 'youtube.com' in url or 'youtu.be' in url:
            m3u8_link = grab_youtube_m3u8(url)
        else:
            m3u8_link = grab(url)
    return render_template('cc.html', m3u8_link=m3u8_link)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
