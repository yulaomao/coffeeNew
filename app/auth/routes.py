from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.auth import bp


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('auth/login.html')
        
        from app.models.user import User
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.active:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    """Logout."""
    logout_user()
    return redirect(url_for('auth.login'))