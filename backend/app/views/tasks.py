from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('tasks', __name__)

@bp.route('/tasks')
@login_required
def index():
    return render_template('tasks.html')