from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('recipes', __name__)

@bp.route('/recipes')
@login_required
def index():
    return render_template('recipes.html')