from flask import Flask, request, redirect, render_template_string, jsonify, Response
import requests
import time
import threading
import re
app = Flask(__name__)


M3U_FILE_PATH = 'you.m3u'

def read_m3u_file():
    with open(M3U_FILE_PATH, 'r') as file:
        return file.readlines()

def write_m3u_file(lines):
    with open(M3U_FILE_PATH, 'w') as file:
        file.writelines(lines)

@app.route('/you.m3u', methods=['GET'])
def serve_m3u():
    content = ''.join(read_m3u_file())
    return Response(content, mimetype='text/plain')

@app.route('/use', methods=['GET'])
def update_link():
    channel_name = request.args.get('channel')
    new_link = request.args.get('link')

    if not channel_name or not new_link:
        return jsonify({'error': 'Missing parameters'}), 400

    lines = read_m3u_file()
    updated = False

    for i, line in enumerate(lines):
        if line.startswith('#EXTINF') and channel_name in line:
            # Skip the `#EXTINF` line and replace the next line with the new link
            if i + 1 < len(lines):
                lines[i + 1] = new_link + '\n'
                updated = True
                break

    if updated:
        write_m3u_file(lines)
        return jsonify({'message': 'Link updated successfully'})
    else:
        return jsonify({'error': 'Channel not found'}), 404

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

# আইডি এবং চ্যানেলের নামের তালিকা
channels = [
    "ISLAM BANGLA&UCN6sm8iHiPd0cnoUardDAnw",
    "Bangla TV&288uue2737",
    "Nd TV&828jej263"
]

# রিকোয়েস্ট স্ট্যাটাসের জন্য একটি লিস্ট
request_status = []

# নির্দিষ্ট রিকোয়েস্ট পাঠানোর ফাংশন
def send_request(channel_name, channel_id):
    base_url_youtube = "https://dc641bf7-026f-48d9-9921-7c77ad2ee137-00-3ijnparc2238r.sisko.replit.dev/youtube?live&id="
    base_url_use = "https://dc641bf7-026f-48d9-9921-7c77ad2ee137-00-3ijnparc2238r.sisko.replit.dev/use?channel="

    # প্রথম রিকোয়েস্ট পাঠানো
    youtube_link = f"{base_url_youtube}{channel_id}.m3u8"
    response = requests.get(youtube_link)

    if response.status_code == 200:
        redirected_link = response.url  # প্রাপ্ত লিংক

        # দ্বিতীয় রিকোয়েস্ট পাঠানো
        use_link = f"{base_url_use}{channel_name}&link={redirected_link}"
        use_response = requests.get(use_link)

        if use_response.status_code == 200:
            # সাকসেসফুল স্ট্যাটাস সংরক্ষণ
            request_status.append({
                'channel': channel_name,
                'id': channel_id,
                'status': 'Success'
            })
            print(f"Successfully sent link for {channel_name}")
        else:
            # ব্যর্থতার স্ট্যাটাস সংরক্ষণ
            request_status.append({
                'channel': channel_name,
                'id': channel_id,
                'status': 'Failed'
            })
            print(f"Failed to send link for {channel_name}, status code: {use_response.status_code}")
    else:
        # ব্যর্থতার স্ট্যাটাস সংরক্ষণ
        request_status.append({
            'channel': channel_name,
            'id': channel_id,
            'status': 'Failed'
        })
        print(f"Failed to get redirected link for {channel_name}, status code: {response.status_code}")

# প্রতি এক মিনিট অন্তর রিকোয়েস্ট পাঠানোর জন্য ফাংশন
def background_task():
    while True:
        for channel_info in channels:
            # চ্যানেলের নাম এবং আইডি আলাদা করা
            channel_name, channel_id = channel_info.split("&")
            send_request(channel_name, channel_id)
        time.sleep(3600)

# প্রতি ৫ মিনিটে স্ট্যাটাস ক্লিয়ার করার ফাংশন
def clear_status():
    while True:
        time.sleep(300)  # ৫ মিনিট (৩০০ সেকেন্ড)
        request_status.clear()
        print("Cleared request statuses")

# Flask অ্যাপের route
@app.route('/see')
def index():
    # JSON হিসেবে রিকোয়েস্ট স্ট্যাটাস দেখানো
    return jsonify(request_status)

# ব্যাকগ্রাউন্ড টাস্ক চালু করা
if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে রিকোয়েস্ট পাঠানোর টাস্ক
    threading.Thread(target=background_task).start()

    # প্রতি ৫ মিনিটে স্ট্যাটাস ক্লিয়ার করার টাস্ক
    threading.Thread(target=clear_status).start()

    # Flask অ্যাপ চালানো
    app.run(host='0.0.0.0', port=5000, debug=True)
