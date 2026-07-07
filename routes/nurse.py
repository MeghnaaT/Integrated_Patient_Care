# =============================================================================
# routes/nurse.py — Nurse Blueprint
# =============================================================================
# URL prefix: /nurse  (set in app.py)
# Requires:   role == 'Nurse'
# =============================================================================

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from utils.decorators import role_required
from models.patient import Patient
from models.appointment import Appointment

nurse_bp = Blueprint('nurse', __name__)


@nurse_bp.route('/dashboard')
@login_required
@role_required('Nurse')
def dashboard():
    """Nurse home — active patient list and today's appointment schedule."""
    from models.nurse import Nurse
    nurse = Nurse.query.get(current_user.id)

    all_patients = Patient.query.order_by(Patient.last_name.asc()).all()

    today_appointments = (
        Appointment.query
        .filter(Appointment.status.in_(['Pending', 'Confirmed']))
        .order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
        .limit(20)
        .all()
    )

    context = {
        'title':              'Nurse Dashboard',
        'nurse':              nurse,
        'all_patients':       all_patients,
        'today_appointments': today_appointments,
    }
    return render_template('dashboards/nurse.html', **context)
