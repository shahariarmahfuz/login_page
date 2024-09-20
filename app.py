from flask import Flask, render_template, redirect, url_for, jsonify, send_from_directory, request, render_template_string, Response, session
import os
import importlib
import requests
import threading
import time
import re
import random
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key'
# Automatically register all blueprints from the 'blueprints' folder
def register_blueprints(app):
    blueprints_dir = os.path.join(os.path.dirname(__file__), 'blueprints')

    for filename in os.listdir(blueprints_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = f"blueprints.{filename[:-3]}"
            module = importlib.import_module(module_name)
            blueprint = getattr(module, f"{filename[:-3]}_blueprint")
            app.register_blueprint(blueprint)

register_blueprints(app)

# Serve JavaScript files from 'scripts' folder
@app.route('/scripts/<path:filename>')
def serve_scripts(filename):
    return send_from_directory('scripts', filename)

# Serve static files (CSS, images, etc.) from 'static' folder
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Custom 404 Error Handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Keep-Alive route
@app.route('/keep_alive')
def keep_alive():
    return "I'm alive!", 200

# Function to periodically ping the Keep-Alive route
def keep_alive_task():
    while True:
        try:
            response = requests.get('https://nekotools.onrender.com/keep_alive')
            if response.status_code == 200:
                print("Keep-alive ping sent successfully.")
            else:
                print(f"Keep-alive ping failed with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send keep-alive ping: {e}")
        time.sleep(300)

# Multiple M3U URLs
m3u_urls = {
    "Link 1": "https://raw.githubusercontent.com/FunctionError/PiratesTv/main/combined_playlist.m3u",
    "Link 2": "https://nekotools.onrender.com/you.m3u",
}

# Function to parse the m3u file and extract channel information
def parse_m3u(m3u_url):
    response = requests.get(m3u_url)
    content = response.text

    # Regex to extract channel details and URLs
    pattern = re.compile(r'#EXTINF:-1.*?tvg-logo="(.*?)".*?group-title="(.*?)".*?,(.*?)\n(.*?)\n')
    channels = []
    
    matches = pattern.findall(content)
    for match in matches:
        logo, group_title, channel_name, stream_url = match
        channels.append({
            "name": channel_name,
            "logo": logo,
            "group": group_title,
            "url": stream_url
        })

    return channels

# Home route to show M3U options and default to the first M3U link
@app.route('/channel')
def home_channel():
    default_link = next(iter(m3u_urls.keys()))
    selected_link = request.args.get('link', default_link)
    
    channels = parse_m3u(m3u_urls[selected_link])
    
    # Group channels by their group-title
    grouped_channels = {}
    for channel in channels:
        group = channel["group"]
        if group not in grouped_channels:
            grouped_channels[group] = []
        grouped_channels[group].append(channel)
    
    return render_template('index.html', m3u_urls=m3u_urls, grouped_channels=grouped_channels, selected_link=selected_link)

# Route to load a specific channel
@app.route('/channel/<link_name>/<channel_name>')
def view_channel(link_name, channel_name):
    m3u_url = m3u_urls.get(link_name)
    if not m3u_url:
        return "Invalid M3U link", 404
    
    channels = parse_m3u(m3u_url)

    # Find the channel details by name
    channel = next((ch for ch in channels if ch['name'] == channel_name), None)

    if channel:
        # Get related channels from the same group
        related_channels = [ch for ch in channels if ch['group'] == channel['group'] and ch['name'] != channel_name]
        # Limit the number of related channels to 5
        related_channels = related_channels[:5]
        return render_template('channel.html', channel=channel, related_channels=related_channels, link_name=link_name)
    else:
        return "Channel not found", 404

# Route to fetch channels for a given M3U link
@app.route('/channels/<link_name>')
def fetch_channels(link_name):
    m3u_url = m3u_urls.get(link_name)
    if not m3u_url:
        return jsonify({'error': 'Invalid M3U link'}), 404

    channels = parse_m3u(m3u_url)
    
    # Group channels by their group-title
    grouped_channels = {}
    for channel in channels:
        group = channel["group"]
        if group not in grouped_channels:
            grouped_channels[group] = []
        grouped_channels[group].append(channel)

    return jsonify({'grouped_channels': [{'group': group, 'channels': channels} for group, channels in grouped_channels.items()]})

# Start the keep-alive thread when the Flask app starts
@app.route('/source', methods=['GET'])
def get_source():
    url = request.args.get('url')  # GET method using request.args
    if url:
        try:
            response = requests.get(url)
            source_code = response.text
            return render_template('get.html', source_code=source_code)
        except Exception as e:
            return "Error fetching the source code."
    else:
        return render_template('get.html')
        
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
    "RTV NEWS&UC2P5Fd5g41Gtdqf0Uzh8Qaw",
    "JAMUNA&UCN6sm8iHiPd0cnoUardDAnw",
    "ATN&UC9Rgo0CrNyd7OWliLekqqGA",
"MADANI&UC0AMtPKwU61uDs--L04_kfQ"
]

# রিকোয়েস্ট স্ট্যাটাসের জন্য একটি লিস্ট
request_status = []

# নির্দিষ্ট রিকোয়েস্ট পাঠানোর ফাংশন
def send_request(channel_name, channel_id, failed_channels):
    base_url_youtube = "https://psychic-succotash-three.vercel.app/youtube?live&id="
    base_url_use = "https://nekotools.onrender.com/use?channel="

    # প্রথম রিকোয়েস্ট পাঠানো
    youtube_link = f"{base_url_youtube}{channel_id}.m3u8"
    response = requests.get(youtube_link)

    if response.status_code == 200:
        redirected_link = response.url  # প্রাপ্ত লিংক

        # ১৫ সেকেন্ড অপেক্ষা করুন
        time.sleep(15)

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
            # ব্যর্থতার স্ট্যাটাস সংরক্ষণ এবং failed_channels এ যুক্ত করা
            request_status.append({
                'channel': channel_name,
                'id': channel_id,
                'status': 'Failed'
            })
            failed_channels.append(channel_name)  # Add to failed channels
            print(f"Failed to send link for {channel_name}, status code: {use_response.status_code}")
    else:
        # ব্যর্থতার স্ট্যাটাস সংরক্ষণ এবং failed_channels এ যুক্ত করা
        request_status.append({
            'channel': channel_name,
            'id': channel_id,
            'status': 'Failed'
        })
        failed_channels.append(channel_name)  # Add to failed channels
        print(f"Failed to get redirected link for {channel_name}, status code: {response.status_code}")

# প্রতি এক মিনিট অন্তর রিকোয়েস্ট পাঠানোর জন্য ফাংশন
def background_task():
    while True:
        failed_channels = []  # Failed channels list

        # প্রথমবারের জন্য সমস্ত চ্যানেল প্রক্রিয়া করা
        for channel_info in channels:
            channel_name, channel_id = channel_info.split("&")
            send_request(channel_name, channel_id, failed_channels)
            # ৩০ সেকেন্ড অপেক্ষা করুন
            time.sleep(30)

        # যদি কোন চ্যানেল ফেল হয় তবে পুনরায় চেষ্টা করুন
        if failed_channels:
            print("Retrying failed channels...")
            for channel_name in failed_channels:
                channel_id = next(id for name, id in (info.split("&") for info in channels) if name == channel_name)
                send_request(channel_name, channel_id, [])
                # ৩০ সেকেন্ড অপেক্ষা করুন
                time.sleep(30)

        # প্রতি ঘণ্টায় একবার সমস্ত চ্যানেল প্রক্রিয়া করা হবে
        time.sleep(3600)

# প্রতি ৩০ মিনিটে স্ট্যাটাস ক্লিয়ার করার ফাংশন
def clear_status():
    while True:
        time.sleep(3540)  # ৩০ মিনিট (১৮০০ সেকেন্ড)
        request_status.clear()
        print("Cleared request statuses")

# Flask অ্যাপের route
@app.route('/see')
def see_status():
    # JSON হিসেবে রিকোয়েস্ট স্ট্যাটাস দেখানো
    return jsonify(request_status)

user_requests = {}

# Function to generate random ID
def generate_random_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

# Home route to render the HTML form
@app.route('/translate')
def translate():
    # Check if the user has an ID in the session
    if 'user_id' not in session:
        session['user_id'] = generate_random_id()

    unique_id = session['user_id']
    translate_option = request.args.get('translate_option', '')
    translated_text = ''
    user_text = ''

    if unique_id in user_requests:
        # Retrieve the user text from the storage
        user_text = user_requests.get(unique_id, {}).get('text', '')
        translate_option = user_requests.get(unique_id, {}).get('translate_option', '')

        if user_text and translate_option:
            # Map the translation option to the correct API endpoint
            api_urls = {
                'Bangla to Banglish': f"https://symmetrical-octo-potato.vercel.app/ask?q={user_text}&id={generate_random_id()}",
                'Any to Hinglish': f"https://symmetrical-octo-potato.vercel.app/hi?q={user_text}&id={generate_random_id()}",
                'Any to English': f"https://symmetrical-octo-potato.vercel.app/en?q={user_text}&id={generate_random_id()}",
                'Any to Bangla': f"https://symmetrical-octo-potato.vercel.app/bn?q={user_text}&id={generate_random_id()}"
            }

            # Get the API URL based on user selection
            api_url = api_urls.get(translate_option)

            # Make the API request
            response = requests.get(api_url)
            translated_text = response.json().get('response', 'Translation not available')

        # Remove the request data after processing
        # Once the text is translated and shown, we remove the user data from the server
        user_requests.pop(unique_id, None)

    return render_template('translator.html', translated_text=translated_text, user_text=user_text, translate_option=translate_option, user_id=unique_id)

# Route to handle form submission
@app.route('/submit', methods=['GET'])
def submit():
    user_text = request.args.get('text', '')
    translate_option = request.args.get('translate_option', '')

    if user_text and translate_option:
        unique_id = session.get('user_id')
        user_requests[unique_id] = {
            'text': user_text,
            'translate_option': translate_option
        }
        return redirect(url_for('translate'))

    return redirect(url_for('translate'))

# Route to change user ID manually
@app.route('/change_id', methods=['GET'])
def change_id():
    session['user_id'] = generate_random_id()
    return redirect(url_for('translate'))

API_KEY = 'ab2c4df280e465bab4875b51'

currencies = [
    ("🇧🇩", "BDT", "Bangladeshi Taka"),
    ("🇦🇪", "AED", "United Arab Emirates Dirham"),
    ("🇦🇫", "AFN", "Afghan Afghani"),
    ("🇦🇱", "ALL", "Albanian Lek"),
    ("🇦🇲", "AMD", "Armenian Dram"),
    ("🇧🇶", "ANG", "Netherlands Antillean Guilder"),
    ("🇦🇴", "AOA", "Angolan Kwanza"),
    ("🇦🇷", "ARS", "Argentine Peso"),
    ("🇦🇺", "AUD", "Australian Dollar"),
    ("🇦🇼", "AWG", "Aruban Florin"),
    ("🇦🇿", "AZN", "Azerbaijani Manat"),
    ("🇧🇦", "BAM", "Bosnia-Herzegovina Convertible Mark"),
    ("🇧🇧", "BBD", "Barbadian Dollar"),
    ("🇧🇬", "BGN", "Bulgarian Lev"),
    ("🇧🇭", "BHD", "Bahraini Dinar"),
    ("🇧🇮", "BIF", "Burundian Franc"),
    ("🇧🇲", "BMD", "Bermudian Dollar"),
    ("🇧🇬", "BND", "Brunei Dollar"),
    ("🇧🇴", "BOB", "Bolivian Boliviano"),
    ("🇧🇷", "BRL", "Brazilian Real"),
    ("🇧🇸", "BSD", "Bahamian Dollar"),
    ("🇧🇹", "BTN", "Bhutanese Ngultrum"),
    ("🇧🇼", "BWP", "Botswana Pula"),
    ("🇧🇾", "BYN", "Belarusian Ruble"),
    ("🇧🇿", "BZD", "Belize Dollar"),
    ("🇨🇦", "CAD", "Canadian Dollar"),
    ("🇨🇩", "CDF", "Congolese Franc"),
    ("🇨🇭", "CHF", "Swiss Franc"),
    ("🇨🇱", "CLP", "Chilean Peso"),
    ("🇨🇳", "CNY", "Chinese Yuan"),
    ("🇨🇴", "COP", "Colombian Peso"),
    ("🇨🇷", "CRC", "Costa Rican Colón"),
    ("🇨🇺", "CUP", "Cuban Peso"),
    ("🇨🇻", "CVE", "Cape Verdean Escudo"),
    ("🇨🇿", "CZK", "Czech Koruna"),
    ("🇩🇯", "DJF", "Djiboutian Franc"),
    ("🇩🇰", "DKK", "Danish Krone"),
    ("🇩🇴", "DOP", "Dominican Peso"),
    ("🇩🇿", "DZD", "Algerian Dinar"),
    ("🇪🇬", "EGP", "Egyptian Pound"),
    ("🇪🇷", "ERN", "Eritrean Nakfa"),
    ("🇪🇹", "ETB", "Ethiopian Birr"),
    ("🇪🇺", "EUR", "Euro"),
    ("🇫🇯", "FJD", "Fijian Dollar"),
    ("🇫🇰", "FKP", "Falkland Islands Pound"),
    ("🇫🇴", "FOK", "Faroese Króna"),
    ("🇬🇧", "GBP", "British Pound Sterling"),
    ("🇬🇪", "GEL", "Georgian Lari"),
    ("🇬🇬", "GGP", "Guernsey Pound"),
    ("🇬🇭", "GHS", "Ghanaian Cedi"),
    ("🇬🇮", "GIP", "Gibraltar Pound"),
    ("🇬🇲", "GMD", "Gambian Dalasi"),
    ("🇬🇳", "GNF", "Guinean Franc"),
    ("🇬🇹", "GTQ", "Guatemalan Quetzal"),
    ("🇬🇾", "GYD", "Guyanese Dollar"),
    ("🇭🇰", "HKD", "Hong Kong Dollar"),
    ("🇭🇳", "HNL", "Honduran Lempira"),
    ("🇭🇷", "HRK", "Croatian Kuna"),
    ("🇭🇹", "HTG", "Haitian Gourde"),
    ("🇭🇺", "HUF", "Hungarian Forint"),
    ("🇮🇩", "IDR", "Indonesian Rupiah"),
    ("🇮🇱", "ILS", "Israeli New Shekel"),
    ("🇮🇲", "IMP", "Isle of Man Pound"),
    ("🇮🇳", "INR", "Indian Rupee"),
    ("🇮🇶", "IQD", "Iraqi Dinar"),
    ("🇮🇮", "IRR", "Iranian Rial"),
    ("🇮🇸", "ISK", "Icelandic Króna"),
    ("🇯🇪", "JEP", "Jersey Pound"),
    ("🇯🇲", "JMD", "Jamaican Dollar"),
    ("🇯🇴", "JOD", "Jordanian Dinar"),
    ("🇯🇵", "JPY", "Japanese Yen"),
    ("🇰🇪", "KES", "Kenyan Shilling"),
    ("🇰🇬", "KGS", "Kyrgyzstani Som"),
    ("🇰🇭", "KHR", "Cambodian Riel"),
    ("🇰🇶", "KID", "Kiribati Dollar"),
    ("🇰🇫", "KMF", "Comorian Franc"),
    ("🇰🇷", "KRW", "South Korean Won"),
    ("🇰🇼", "KWD", "Kuwaiti Dinar"),
    ("🇰🇾", "KYD", "Cayman Islands Dollar"),
    ("🇰🇿", "KZT", "Kazakhstani Tenge"),
    ("🇱🇦", "LAK", "Lao Kip"),
    ("🇱🇧", "LBP", "Lebanese Pound"),
    ("🇱🇰", "LKR", "Sri Lankan Rupee"),
    ("🇱🇷", "LRD", "Liberian Dollar"),
    ("🇱🇸", "LSL", "Lesotho Loti"),
    ("🇱🇾", "LYD", "Libyan Dinar"),
    ("🇲🇦", "MAD", "Moroccan Dirham"),
    ("🇲🇩", "MDL", "Moldovan Leu"),
    ("🇲🇬", "MGA", "Malagasy Ariary"),
    ("🇲🇰", "MKD", "Macedonian Denar"),
    ("🇲🇲", "MMK", "Myanmar Kyat"),
    ("🇲🇳", "MNT", "Mongolian Tögrög"),
    ("🇲🇴", "MOP", "Macanese Pataca"),
    ("🇲🇷", "MRU", "Mauritanian Ouguiya"),
    ("🇲🇺", "MUR", "Mauritian Rupee"),
    ("🇲🇻", "MVR", "Maldivian Rufiyaa"),
    ("🇲🇼", "MWK", "Malawian Kwacha"),
    ("🇲🇽", "MXN", "Mexican Peso"),
    ("🇲🇾", "MYR", "Malaysian Ringgit"),
    ("🇲🇿", "MZN", "Mozambican Metical"),
    ("🇳🇦", "NAD", "Namibian Dollar"),
    ("🇳🇬", "NGN", "Nigerian Naira"),
    ("🇳🇮", "NIO", "Nicaraguan Córdoba"),
    ("🇳🇴", "NOK", "Norwegian Krone"),
    ("🇳🇵", "NPR", "Nepalese Rupee"),
    ("🇳🇿", "NZD", "New Zealand Dollar"),
    ("🇴🇲", "OMR", "Omani Rial"),
    ("🇵🇦", "PAB", "Panamanian Balboa"),
    ("🇵🇪", "PEN", "Peruvian Sol"),
    ("🇵🇬", "PGK", "Papua New Guinean Kina"),
    ("🇵🇭", "PHP", "Philippine Peso"),
    ("🇵🇰", "PKR", "Pakistani Rupee"),
    ("🇵🇱", "PLN", "Polish Zloty"),
    ("🇵🇾", "PYG", "Paraguayan Guarani"),
    ("🇶🇦", "QAR", "Qatari Rial"),
    ("🇷🇴", "RON", "Romanian Leu"),
    ("🇷🇸", "RSD", "Serbian Dinar"),
    ("🇷🇺", "RUB", "Russian Ruble"),
    ("🇷🇼", "RWF", "Rwandan Franc"),
    ("🇸🇦", "SAR", "Saudi Riyal"),
    ("🇸🇧", "SBD", "Solomon Islands Dollar"),
    ("🇸🇨", "SCR", "Seychellois Rupee"),
    ("🇸🇩", "SDG", "Sudanese Pound"),
    ("🇸🇪", "SEK", "Swedish Krona"),
    ("🇸🇬", "SGD", "Singapore Dollar"),
    ("🇸🇭", "SHP", "Saint Helena Pound"),
    ("🇸🇱", "SLE", "Sierra Leonean Leone"),
    ("🇸🇬", "SLL", "Sierra Leonean Leone"),
    ("🇸🇧", "SOS", "Somali Shilling"),
    ("🇸🇷", "SRD", "Surinamese Dollar"),
    ("🇸🇸", "SSP", "South Sudanese Pound"),
    ("🇸🇹", "STN", "São Tomé and Príncipe Dobra"),
    ("🇸🇾", "SYP", "Syrian Pound"),
    ("🇿🇦", "ZAR", "South African Rand"),
    ("🇿🇼", "ZWL", "Zimbabwean Dollar"),
]


@app.route('/currency', methods=['GET'])
def currency_converter():
    from_currency = request.args.get('from_currency', '')
    to_currency = request.args.get('to_currency', '')
    amount = request.args.get('amount', '')

    result = ''
    if from_currency and to_currency and amount:
        # API থেকে রূপান্তরের রেট নেওয়া
        url = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{from_currency}'
        response = requests.get(url)
        data = response.json()

        if data['result'] == 'success':
            conversion_rate = data['conversion_rates'][to_currency]
            converted_amount = float(amount) * conversion_rate
            result = f"{amount} {from_currency} = {converted_amount:.2f} {to_currency}"
        else:
            result = "Conversion rate not available."

    return render_template('currency.html', currencies=currencies, result=result, 
                           from_currency=from_currency, to_currency=to_currency, amount=amount)
                           
if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে রিকোয়েস্ট পাঠানোর টাস্ক
    threading.Thread(target=background_task).start()

    # প্রতি ৩০ মিনিটে স্ট্যাটাস ক্লিয়ার করার টাস্ক
    threading.Thread(target=clear_status).start()

    # Flask অ্যাপ চালানো
    threading.Thread(target=keep_alive_task, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
