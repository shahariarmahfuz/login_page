from flask import Blueprint, render_template, request
import requests

iplookup_blueprint = Blueprint('iplookup', __name__, template_folder='templates')

@iplookup_blueprint.route('/lookup', methods=['GET'])
def lookup():
    ip_info = None
    ip_address = request.args.get('ip_address')
    if ip_address:
        response = requests.get(f'http://ip-api.com/json/{ip_address}')
        ip_info = response.json()
    return render_template('iplookup.html', ip_info=ip_info)
