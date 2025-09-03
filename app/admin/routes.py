from flask import render_template, request, jsonify
from flask_login import login_required
from app.admin import bp


@bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page."""
    return render_template('admin/dashboard.html')


@bp.route('/devices')
@login_required  
def devices():
    """Devices management page."""
    # Get query parameters for filtering
    query = request.args.get('query', '')
    status = request.args.get('status', '')
    model = request.args.get('model', '')
    return render_template('admin/devices.html', query=query, status=status, model=model)


@bp.route('/devices/<device_id>')
@login_required
def device_detail(device_id):
    """Device detail page."""
    return render_template('admin/device_detail.html', device_id=device_id)


@bp.route('/orders')
@login_required
def orders():
    """Orders management page."""
    # Get query parameters for filtering
    from_date = request.args.get('from', '')
    to_date = request.args.get('to', '')
    device_id = request.args.get('device_id', '')
    payment_method = request.args.get('payment_method', '')
    exception = request.args.get('exception', '')
    
    return render_template('admin/orders.html', 
                         from_date=from_date, 
                         to_date=to_date,
                         device_id=device_id,
                         payment_method=payment_method,
                         exception=exception)


@bp.route('/materials')
@login_required
def materials():
    """Materials management page."""
    return render_template('admin/materials.html')


@bp.route('/recipes')
@login_required
def recipes():
    """Recipes management page."""
    return render_template('admin/recipes.html')


@bp.route('/alarms')
@login_required
def alarms():
    """Alarms management page."""
    return render_template('admin/alarms.html')


@bp.route('/tasks')
@login_required
def tasks():
    """Tasks management page."""
    return render_template('admin/tasks.html')


@bp.route('/audit')
@login_required
def audit():
    """Audit log page."""
    return render_template('admin/audit.html')