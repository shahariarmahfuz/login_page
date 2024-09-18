import requests
from flask import Blueprint, render_template, request, redirect, url_for, session
import random
import string

translator_blueprint = Blueprint('translator', __name__, template_folder='templates')

# In-memory storage for user requests
user_requests = {}

# Function to generate random ID
def generate_random_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

# Home route to render the HTML form
@translator_blueprint.route('/translate')
def translator():
    if 'user_id' not in session:
        session['user_id'] = generate_random_id()

    unique_id = session['user_id']
    translate_option = request.args.get('translate_option', '')
    translated_text = ''
    user_text = ''

    if unique_id in user_requests:
        user_text = user_requests.get(unique_id, {}).get('text', '')
        translate_option = user_requests.get(unique_id, {}).get('translate_option', '')

        if user_text and translate_option:
            api_urls = {
                'Bangla to Banglish': f"https://symmetrical-octo-potato.vercel.app/ask?q={user_text}&id={generate_random_id()}",
                'Any to Hinglish': f"https://symmetrical-octo-potato.vercel.app/hi?q={user_text}&id={generate_random_id()}",
                'Any to English': f"https://symmetrical-octo-potato.vercel.app/en?q={user_text}&id={generate_random_id()}",
                'Any to Bangla': f"https://symmetrical-octo-potato.vercel.app/bn?q={user_text}&id={generate_random_id()}"
            }

            api_url = api_urls.get(translate_option)
            response = requests.get(api_url)
            translated_text = response.json().get('response', 'Translation not available')

        user_requests.pop(unique_id, None)

    return render_template('translator.html', translated_text=translated_text, user_text=user_text, translate_option=translate_option, user_id=unique_id)

# Route to handle form submission
@translator_blueprint.route('/submit', methods=['GET'])
def submit():
    user_text = request.args.get('text', '')
    translate_option = request.args.get('translate_option', '')

    if user_text and translate_option:
        unique_id = session.get('user_id')
        user_requests[unique_id] = {
            'text': user_text,
            'translate_option': translate_option
        }
        return redirect(url_for('translator.translator'))

    return redirect(url_for('translator.translator'))

# Route to change user ID manually
@translator_blueprint.route('/change_id', methods=['GET'])
def change_id():
    session['user_id'] = generate_random_id()
    return redirect(url_for('translator.translator'))
