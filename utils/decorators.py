# =============================================================================
# utils/decorators.py — Custom Route Decorators
# =============================================================================
# role_required(*role_names)
#   — Wraps a view function and aborts with 403 if the current user's role
#     does not match any of the required role name strings.
#   — Must be applied AFTER @login_required so current_user is always valid.
#
# Usage:
#   @admin_bp.route('/dashboard')
#   @login_required
#   @role_required('Admin', 'Doctor')
#   def dashboard():
#       ...
# =============================================================================

from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*role_names: str):
    """
    Decorator factory that enforces role-based access control.

    Args:
        *role_names: Exact role name strings allowed (e.g. 'Admin', 'Doctor', 'Nurse').

    Returns:
        A decorator that wraps the view function.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = current_user.role.name if (current_user.is_authenticated and current_user.role) else None
            if user_role not in role_names:
                abort(403)   # Triggers the 403 error handler
            return f(*args, **kwargs)
        return decorated_function
    return decorator
