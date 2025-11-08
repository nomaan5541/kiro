"""
Authentication utilities for session-based authentication
"""
from functools import wraps
from flask import session, redirect, url_for, flash, g
from models.user import User


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(required_role):
    """Decorator to require specific role for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page', 'error')
                return redirect(url_for('auth.login'))
            
            if session.get('user_role') != required_role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """Get current user from session"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def before_request():
    """Load current user before each request"""
    g.current_user = get_current_user()