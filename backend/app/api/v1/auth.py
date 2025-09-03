from flask import request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app.api.v1 import bp
from app.api.response import success_response, error_response, ErrorCode
from app.models import User
from app.extensions import db


@bp.route('/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return error_response(
                ErrorCode.MISSING_REQUIRED_FIELD,
                "Email and password are required"
            )
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']) and user.is_active():
            login_user(user)
            return success_response({
                "user": user.to_dict(),
                "message": "Login successful"
            })
        else:
            return error_response(
                ErrorCode.UNAUTHORIZED,
                "Invalid email or password",
                status_code=401
            )
    
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Login failed: {str(e)}",
            status_code=500
        )


@bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """User logout"""
    try:
        logout_user()
        return success_response({"message": "Logout successful"})
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Logout failed: {str(e)}",
            status_code=500
        )


@bp.route('/auth/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    try:
        return success_response(current_user.to_dict())
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get user info: {str(e)}",
            status_code=500
        )