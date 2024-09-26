from flask import Blueprint, render_template, request
import requests

facebook_blueprint = Blueprint('facebook', __name__, template_folder='templates')

@facebook_blueprint.route('/Facebook', methods=['GET', 'POST'])
def facebook():  # It’s common to have route function names in lowercase
    result = None
    if request.method == 'POST':
        video_url = request.form['url']
        api_url = f"https://facebook-reel-and-video-downloader.p.rapidapi.com/app/main.php?url={video_url}"
        
        headers = {
            'x-rapidapi-host': 'facebook-reel-and-video-downloader.p.rapidapi.com',
            'x-rapidapi-key': '80f0a59b76msh49bd109c53bf5a9p1c1366jsn57f6e67af29d'
        }
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
        else:
            result = "Error fetching data from API."
    
    return render_template('Facebook.html', result=result)
