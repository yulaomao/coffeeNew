from flask import render_template, redirect, url_for
from app.main import bp


@bp.route('/')
def index():
    """Main page - redirect to dashboard."""
    return redirect(url_for('admin.dashboard'))


@bp.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'healthy', 'service': 'coffee_admin'}