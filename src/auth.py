"""Authentication decorators and utilities for Flask app."""

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Decorator to require user to be logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def check_session():
    """Check if user is logged in."""
    return 'user_email' in session


def get_current_user():
    """Get current logged-in user from session."""
    if 'user_email' in session:
        return session['user_email']
    return None
