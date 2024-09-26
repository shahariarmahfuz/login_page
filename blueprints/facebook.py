from flask import Blueprint, render_template, request, redirect
import requests

facebook_blueprint = Blueprint('facebook', __name__, template_folder='templates')

@facebookblueprint.route('/Facebook', methods=['GET'])
def facebook():
    return render_template('Facebook.html', result=None)

@facebook_downloader_blueprint.route('/download', methods=['GET'])
def download():
    video_url = request.args.get('url')
    if not video_url:
        return redirect('/facebook')

    api_url = f"https://facebook-reel-and-video-downloader.p.rapidapi.com/app/main.php?url={video_url}"

    headers = {
        'x-rapidapi-host': 'facebook-reel-and-video-downloader.p.rapidapi.com',
        'x-rapidapi-key': 'YOUR_API_KEY'  # Replace with your actual API key
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        result = response.json()  # assuming the API response is in JSON format
    else:
        result = {"error": "Error fetching data from API."}

    return render_template('Facebook.html', result=result)
