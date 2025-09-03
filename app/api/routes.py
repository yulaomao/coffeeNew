from flask import jsonify
from app.api import bp


@bp.route('/health')
def health():
    """API health check."""
    return jsonify({'ok': True, 'data': {'status': 'healthy', 'version': 'v1'}})


# Placeholder routes for API endpoints
@bp.route('/dashboard/summary')
def dashboard_summary():
    """Dashboard summary endpoint."""
    return jsonify({'ok': True, 'data': {'message': 'Not implemented yet'}})


@bp.route('/devices')
def devices():
    """Devices list endpoint."""
    return jsonify({'ok': True, 'data': {'message': 'Not implemented yet'}})