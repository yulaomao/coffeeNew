from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('audit', __name__)

@bp.route('/audit')
@login_required
def index():
    return render_template('audit.html')