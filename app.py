from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

def get_live_stream_url(channel_id):
    try:
        # চ্যানেলের ইউটিউব পেজের URL
        channel_url = f'https://www.youtube.com/channel/{channel_id}/live'
        response = requests.get(channel_url)
        source_code = response.text

        # লাইভ ভিডিও লিঙ্ক বের করার জন্য
        live_video_pattern = r'https://www\.youtube\.com/watch\?v=[\w-]+'
        video_urls = re.findall(live_video_pattern, source_code)

        if video_urls:
            # প্রথম লাইভ ভিডিও লিঙ্কে M3U8 লিঙ্ক বের করার চেষ্টা করুন
            video_url = video_urls[0]
            m3u8_url = get_m3u8_url(video_url)
            return m3u8_url
        else:
            return None
    except Exception as e:
        return None

def get_m3u8_url(video_url):
    try:
        # ভিডিও পেজের সোর্স কোড থেকে M3U8 লিঙ্ক বের করা
        response = requests.get(video_url)
        source_code = response.text
        m3u8_pattern = r'https://manifest\.googlevideo\.com/api/manifest/hls_variant/expire.*?/file/index\.m3u8'
        m3u8_links = re.findall(m3u8_pattern, source_code)
        return m3u8_links[0] if m3u8_links else None
    except Exception as e:
        return None

@app.route('/youtube', methods=['GET'])
def youtube():
    # URL প্যারামিটার থেকে চ্যানেল আইডি বের করা
    url_id = request.args.get('id')
    if url_id and url_id.endswith('.m3u8'):
        channel_id = url_id.replace('.m3u8', '')
        m3u8_url = get_live_stream_url(channel_id)

        if m3u8_url:
            # m3u8 লিঙ্কটি JSON আকারে ইউজারকে দেখানো হবে
            return jsonify({"m3u8_url": m3u8_url})
        else:
            return jsonify({"error": "No live stream or M3U8 link found for the provided channel ID."})
    else:
        return jsonify({"error": "Invalid format. Make sure the URL ends with .m3u8 and includes a valid channel ID."})

@app.route('/')
def home():
    return '''
        <h1>Welcome</h1>
        <p>Use the following URL format to get the M3U8 link for a live stream:</p>
        <p>https://mywebsite.com/youtube?live&id={channel_id}.m3u8</p>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
