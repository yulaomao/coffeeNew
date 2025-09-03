from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('materials', __name__)

@bp.route('/materials')
@login_required
def index():
    return render_template('materials.html')