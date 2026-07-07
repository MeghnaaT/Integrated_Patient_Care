# =============================================================================
# routes/doctor.py — Doctor Blueprint
# =============================================================================
# URL prefix: /doctor  (set in app.py)
# Requires:   role == 'Doctor'
# =============================================================================

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from utils.decorators import role_required
from models.appointment import Appointment
from models.medical_record import MedicalRecord

doctor_bp = Blueprint('doctor', __name__)


@doctor_bp.route('/dashboard')
@login_required
@role_required('Doctor')
def dashboard():
    """Doctor home — upcoming appointments and recent EHR activity."""
    from models.doctor import Doctor
    doctor = Doctor.query.get(current_user.id)

    upcoming_appointments = (
        Appointment.query
        .filter_by(doctor_id=current_user.id, status='Confirmed')
        .order_by(Appointment.appointment_date.asc())
        .limit(10)
        .all()
    )

    recent_records = (
        MedicalRecord.query
        .filter_by(doctor_id=current_user.id)
        .order_by(MedicalRecord.visit_date.desc())
        .limit(5)
        .all()
    )

    context = {
        'title':                 'Doctor Dashboard',
        'doctor':                doctor,
        'upcoming_appointments': upcoming_appointments,
        'recent_records':        recent_records,
    }
    return render_template('dashboards/doctor.html', **context)
