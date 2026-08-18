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
        'Pharmacist': 'pharmacy.dashboard',
        'Laboratory Staff': 'laboratory.list_reports',
        'Receptionist': 'appointment.list_appointments',
    }

    target = role_map.get(role_name, 'auth.login')
    return redirect(url_for(target))


@dashboard_bp.route('/milestone2-dashboard')
@login_required
def milestone2_dashboard():
    """Milestone 2 Overview Dashboard (matches Slide 51 mockup)."""
    from models.patient import Patient
    from models.consultation import Consultation
    from models.prescription import Prescription
    from models.lab_report import LabReport
    from services.consultation_service import get_recent_consultations
    from services.prescription_service import get_recent_prescriptions
    from services.lab_service import get_recent_lab_reports
    from forms.search_form import PatientSearchForm

    total_patients = Patient.query.count()
    total_consultations = Consultation.query.count()
    total_prescriptions = Prescription.query.count()
    total_labs = LabReport.query.count()
    total_reports = total_consultations + total_prescriptions + total_labs

    recent_consultations = get_recent_consultations(limit=5)
    recent_prescriptions = get_recent_prescriptions(limit=5)
    recent_labs = get_recent_lab_reports(limit=5)

    search_form = PatientSearchForm()

    context = {
        'title': 'Milestone 2 Dashboard',
        'total_patients': total_patients,
        'total_consultations': total_consultations,
        'total_prescriptions': total_prescriptions,
        'total_labs': total_labs,
        'total_reports': total_reports,
        'recent_consultations': recent_consultations,
        'recent_prescriptions': recent_prescriptions,
        'recent_labs': recent_labs,
        'search_form': search_form
    }
    return render_template('dashboards/milestone2_dashboard.html', **context)

