from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('devices', __name__)

@bp.route('/devices')
@login_required
def index():
    return render_template('devices.html')