# =============================================================================
# routes/dashboard.py — Root & Role-Dispatcher Blueprint
# =============================================================================
# /             → redirect to login
# /dashboard    → inspect role, redirect to the correct role dashboard
# =============================================================================

from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Landing root — send unauthenticated visitors to login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Central dispatch point.
    Reads current_user.role.name and redirects to the appropriate
    role-specific dashboard blueprint.
    """
    role_name = current_user.role.name if current_user.role else None

    role_map = {
        'Admin':   'admin.dashboard',
        'Doctor':  'doctor.dashboard',
        'Nurse':   'nurse.dashboard',
        'Patient': 'patient.dashboard',
    }

    target = role_map.get(role_name, 'auth.login')
    return redirect(url_for(target))
