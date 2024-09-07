from flask import Blueprint, render_template

password_blueprint = Blueprint('password', __name__, template_folder='../templates')

@password_blueprint.route('/pas')
def password():
    return render_template('password.html')
