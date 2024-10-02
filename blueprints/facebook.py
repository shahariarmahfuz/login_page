from flask import Blueprint, render_template, request
import requests

downloader_blueprint = Blueprint('downloader', __name__, template_folder='../templates')

@downloader_blueprint.route('/fb', methods=['GET'])
def deep_downloader():  # ফাংশনের নতুন নাম
    result = None
    video_url = request.args.get('url')  # Get the URL from the query parameters

    if video_url:
        api_url = f"https://facebook-reel-and-video-downloader.p.rapidapi.com/app/main.php?url={video_url}"
        
        headers = {
            'x-rapidapi-host': 'facebook-reel-and-video-downloader.p.rapidapi.com',
            'x-rapidapi-key': '80f0a59b76msh49bd109c53bf5a9p1c1366jsn57f6e67af29d'
        }
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()  # assuming the API response is in JSON format
        else:
            result = "Error fetching data from API."
    
    return render_template('facebook.html', result=result)
