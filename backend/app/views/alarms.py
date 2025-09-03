from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('alarms', __name__)

@bp.route('/alarms')
@login_required
def index():
    return render_template('alarms.html')