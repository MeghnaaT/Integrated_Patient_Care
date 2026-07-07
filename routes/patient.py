# =============================================================================
# routes/patient.py — Patient Blueprint
# =============================================================================
# URL prefix: /patient  (set in app.py)
# Requires:   role == 'Patient'
# =============================================================================

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from utils.decorators import role_required
from models.appointment import Appointment
from models.medical_record import MedicalRecord

patient_bp = Blueprint('patient', __name__)


@patient_bp.route('/dashboard')
@login_required
@role_required('Patient')
def dashboard():
    """Patient home — personal appointments and medical history overview."""
    from models.patient import Patient
    patient = Patient.query.get(current_user.id)

    my_appointments = (
        Appointment.query
        .filter_by(patient_id=current_user.id)
        .order_by(Appointment.appointment_date.desc())
        .all()
    )

    my_records = (
        MedicalRecord.query
        .filter_by(patient_id=current_user.id)
        .order_by(MedicalRecord.visit_date.desc())
        .limit(5)
        .all()
    )

    context = {
        'title':           'My Dashboard',
        'patient':         patient,
        'my_appointments': my_appointments,
        'my_records':      my_records,
    }
    return render_template('dashboards/patient.html', **context)
