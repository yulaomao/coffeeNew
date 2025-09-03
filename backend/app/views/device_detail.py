from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('device_detail', __name__)

@bp.route('/devices/<device_id>')
@login_required
def detail(device_id):
    return render_template('device_detail.html', device_id=device_id)