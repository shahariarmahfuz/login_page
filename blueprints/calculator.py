from flask import Blueprint, render_template

calculator_blueprint = Blueprint('calculator', __name__, template_folder='../templates')

@calculator_blueprint.route('/age')
def page1():
    return render_template('calculator.html')
