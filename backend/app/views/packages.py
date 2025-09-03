from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('packages', __name__)

@bp.route('/packages')
@login_required
def index():
    return render_template('packages.html')