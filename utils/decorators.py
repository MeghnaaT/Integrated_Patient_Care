# =============================================================================
# utils/decorators.py — Custom Route Decorators
# =============================================================================
# role_required(role_name)
#   — Wraps a view function and aborts with 403 if the current user's role
#     does not match the required role name string.
#   — Must be applied AFTER @login_required so current_user is always valid.
#
# Usage:
#   @admin_bp.route('/dashboard')
#   @login_required
#   @role_required('Admin')
#   def dashboard():
#       ...
# =============================================================================

from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(role_name: str):
    """
    Decorator factory that enforces role-based access control.

    Args:
        role_name: The exact role name string required (e.g. 'Admin', 'Doctor').

    Returns:
        A decorator that wraps the view function.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # current_user is guaranteed to be authenticated (login_required ran first)
            user_role = current_user.role.name if current_user.role else None
            if user_role != role_name:
                abort(403)   # Triggers the 403 error handler registered in app.py
            return f(*args, **kwargs)
        return decorated_function
    return decorator
