from flask import Flask, request, jsonify
import requests
import re
import logging

app = Flask(__name__)

# লগিং সেটআপ করা
logging.basicConfig(level=logging.DEBUG)

def get_live_stream_url(channel_id):
    try:
        # ইউটিউব চ্যানেলের লাইভ পেজের URL
        channel_url = f'https://www.youtube.com/channel/{channel_id}/live'
        logging.debug(f"Channel URL: {channel_url}")
        
        response = requests.get(channel_url)
        html_content = response.text

        # HTML পেজের মেটা ডেটা থেকে লাইভ ভিডিওর লিঙ্ক বের করার প্যাটার্ন
        live_video_pattern = r'\"url\":\"(/watch\?v=[\w-]+)\"'
        video_urls = re.findall(live_video_pattern, html_content)

        if video_urls:
            # ইউটিউব ভিডিওর পূর্ণ লিঙ্ক তৈরি
            video_url = f"https://www.youtube.com{video_urls[0]}"
            logging.debug(f"Live video URL extracted: {video_url}")
            
            m3u8_url = get_m3u8_url(video_url)
            return m3u8_url
        else:
            logging.error(f"No live video found for channel ID: {channel_id}")
            return None
    except Exception as e:
        logging.error(f"Error in get_live_stream_url: {str(e)}")
        return None

def get_m3u8_url(video_url):
    try:
        # ভিডিও পেজ থেকে M3U8 লিঙ্ক বের করা
        logging.debug(f"Fetching video page URL: {video_url}")
        
        response = requests.get(video_url)
        html_content = response.text
        
        # M3U8 লিঙ্ক বের করার জন্য প্যাটার্ন
        m3u8_pattern = r'https://manifest\.googlevideo\.com/api/manifest/hls_variant/expire.*?/file/index\.m3u8'
        m3u8_links = re.findall(m3u8_pattern, html_content)
        
        if m3u8_links:
            logging.debug(f"M3U8 link extracted: {m3u8_links[0]}")
        else:
            logging.error(f"No M3U8 link found in video page: {video_url}")
        
        return m3u8_links[0] if m3u8_links else None
    except Exception as e:
        logging.error(f"Error in get_m3u8_url: {str(e)}")
        return None

@app.route('/youtube', methods=['GET'])
def youtube():
    try:
        # URL প্যারামিটার থেকে চ্যানেল আইডি বের করা, এবং কেবল .m3u8 পর্যন্ত অংশ নেয়া
        url_id = request.args.get('id')
        if url_id:
            logging.debug(f"Raw URL ID received: {url_id}")

            # কেবল .m3u8 দিয়ে শেষ হওয়া অংশ নেওয়া হচ্ছে
            match = re.search(r'([^,;:@\"\'\s]+\.m3u8)$', url_id)
            if match:
                channel_id = match.group(1).replace('.m3u8', '')
                logging.debug(f"Channel ID extracted: {channel_id}")
                
                m3u8_url = get_live_stream_url(channel_id)

                if m3u8_url:
                    return jsonify({"m3u8_url": m3u8_url})
                else:
                    logging.error(f"No live stream or M3U8 link found for channel ID: {channel_id}")
                    return jsonify({"error": "No live stream or M3U8 link found for the provided channel ID."})
            else:
                logging.error(f"Invalid URL format: {url_id}")
                return jsonify({"error": "Invalid format. Ensure the URL ends with .m3u8 and includes a valid channel ID."})
        else:
            logging.error("No URL parameter found")
            return jsonify({"error": "No URL parameter provided."})
    except Exception as e:
        logging.error(f"Error in /youtube route: {str(e)}")
        return jsonify({"error": "An error occurred while processing the request."})

@app.route('/')
def home():
    return '''
        <h1>Welcome</h1>
        <p>Use the following URL format to get the M3U8 link for a live stream:</p>
        <p>https://mywebsite.com/youtube?live&id={channel_id}.m3u8</p>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
