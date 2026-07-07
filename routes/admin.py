# =============================================================================
# routes/admin.py — Admin Blueprint
# =============================================================================
# URL prefix: /admin  (set in app.py)
# Requires:   role == 'Admin'
# =============================================================================

from flask import Blueprint, render_template
from flask_login import login_required

from utils.decorators import role_required
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from models.nurse import Nurse
from models.appointment import Appointment

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
@role_required('Admin')
def dashboard():
    """Admin main dashboard — summary statistics."""
    total_patients = Patient.query.count()
    total_doctors  = Doctor.query.count()
    total_nurses   = Nurse.query.count()
    total_appts    = Appointment.query.count()

    context = {
        'title':          'Admin Dashboard',
        'total_patients': total_patients,
        'total_doctors':  total_doctors,
        'total_nurses':   total_nurses,
        'total_appts':    total_appts,
    }
    return render_template('dashboards/admin.html', **context)
