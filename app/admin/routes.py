from flask import render_template
from flask_login import login_required
from app.admin import bp


@bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page."""
    return render_template('admin/dashboard.html')


# Placeholder routes for admin pages
@bp.route('/devices')
@login_required  
def devices():
    """Devices management page."""
    return render_template('admin/devices.html')


@bp.route('/orders')
@login_required
def orders():
    """Orders management page."""
    return render_template('admin/orders.html')