from flask import Flask, request, jsonify, render_template_string
import requests
import re

app = Flask(__name__)

def get_live_stream_url(channel_id):
    try:
        # চ্যানেলের ইউটিউব পেজের URL
        channel_url = f'https://www.youtube.com/channel/{channel_id}/live'
        response = requests.get(channel_url)
        html_content = response.text

        # লাইভ ভিডিও লিঙ্ক বের করার জন্য
        live_video_pattern = r'https://www\.youtube\.com/watch\?v=[\w-]+'
        video_urls = re.findall(live_video_pattern, html_content)

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
        html_content = response.text
        m3u8_pattern = r'https://manifest\.googlevideo\.com/api/manifest/hls_variant/expire.*?/file/index\.m3u8'
        m3u8_links = re.findall(m3u8_pattern, html_content)
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
            return redirect(m3u8_url)
        else:
            return render_template_string('''
                <h1>No live stream or M3U8 link found for the provided channel ID.</h1>
                <a href="/">Go Back</a>
            ''')
    else:
        return render_template_string('''
            <h1>Invalid format. Make sure the URL ends with .m3u8 and includes a valid channel ID.</h1>
            <a href="/">Go Back</a>
        ''')

@app.route('/get_code', methods=['GET'])
def get_code():
    link = request.args.get('link')
    if link:
        try:
            response = requests.get(link)
            source_code = response.text

            # ইউটিউব চ্যানেল লিঙ্ক খোঁজা
            youtube_channel_pattern = r'https://www\.youtube\.com/channel/([\w-]+)'
            youtube_links = re.findall(youtube_channel_pattern, source_code)
            
            # ডুপ্লিকেট লিঙ্ক বাদ দেওয়া
            unique_links = list(set(youtube_links))
            
            # JSON আকারে ফলাফল প্রদান করা
            return jsonify({
                'youtube_channel_ids': unique_links
            })
        except Exception as e:
            return jsonify({
                'error': 'Error fetching the source code.'
            }), 500
    else:
        return jsonify({
            'error': 'Please provide a valid link.'
        }), 400

@app.route('/')
def home():
    return '''
        <h1>Welcome</h1>
        <p>Use the following URL format to get the M3U8 link for a live stream:</p>
        <p>https://mywebsite.com/youtube?live&id={channel_id}.m3u8</p>
        <p>Use the following URL format to get the YouTube channel IDs from a source URL:</p>
        <p>https://mywebsite.com/get_code?link={source_url}</p>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
