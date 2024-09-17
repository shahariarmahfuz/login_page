from flask import Blueprint, render_template

profile_blueprint = Blueprint('profile', __name__, template_folder='../templates')

@profile_blueprint.route('/')
def email():
    return render_template('profile.html')
