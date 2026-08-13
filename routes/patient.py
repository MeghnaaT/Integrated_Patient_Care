# =============================================================================
# routes/patient.py — Patient Blueprint
# =============================================================================
# URL prefix: /patient  (set in app.py)
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps

from utils.decorators import role_required
from models.appointment import Appointment
from models.medical_record import MedicalRecord
from database.connection import db

patient_bp = Blueprint('patient', __name__)


def roles_required(*role_names: str):
    """Decorator to enforce multiple roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            user_role = current_user.role.name if current_user.role else None
            if user_role not in role_names:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@patient_bp.route('/advanced-search', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse', 'Receptionist', 'Pharmacist')
def advanced_search():
    """Day 1 Advanced Patient Search matching Slide 5 & 6 mockups."""
    from forms.search_form import AdvancedPatientSearchForm
    from models.patient import Patient

    form = AdvancedPatientSearchForm()
    query_str = request.args.get('q', '').strip()
    criteria = request.args.get('criteria', 'all').strip()

    if form.validate_on_submit():
        query_str = form.query.data.strip() if form.query.data else ''
        criteria = form.search_criteria.data

    results = []
    if query_str:
        q = f"%{query_str}%"
        p_query = Patient.query
        if criteria == 'patient_id':
            clean_id = query_str.upper().replace('PAT', '').replace('P', '')
            if clean_id.isdigit():
                p_query = p_query.filter(Patient.id == int(clean_id))
        elif criteria == 'name':
            p_query = p_query.filter((Patient.first_name.ilike(q)) | (Patient.last_name.ilike(q)))
        elif criteria == 'phone':
            p_query = p_query.filter(Patient.phone_number.ilike(q))
        elif criteria == 'aadhaar':
            p_query = p_query.filter(Patient.aadhaar_number.ilike(q))
        elif criteria == 'email':
            p_query = p_query.filter(Patient.email.ilike(q))
        else: # All
            clean_id = query_str.upper().replace('PAT', '').replace('P', '')
            if clean_id.isdigit():
                p_query = p_query.filter(
                    (Patient.id == int(clean_id)) |
                    (Patient.first_name.ilike(q)) |
                    (Patient.last_name.ilike(q)) |
                    (Patient.phone_number.ilike(q)) |
                    (Patient.aadhaar_number.ilike(q)) |
                    (Patient.email.ilike(q))
                )
            else:
                p_query = p_query.filter(
                    (Patient.first_name.ilike(q)) |
                    (Patient.last_name.ilike(q)) |
                    (Patient.phone_number.ilike(q)) |
                    (Patient.aadhaar_number.ilike(q)) |
                    (Patient.email.ilike(q))
                )
        results = p_query.all()
    else:
        results = Patient.query.all()

    return render_template(
        'patients/advanced_search.html',
        form=form,
        patients=results,
        query_str=query_str,
        criteria=criteria,
        title='Patient Search Worklist'
    )


@patient_bp.route('/dashboard')
@login_required
@role_required('Patient')
def dashboard():
    """Patient home — personal appointments, medical history, statistics, and chart data."""
    from models.patient import Patient
    from models.medical_record import MedicalRecord
    import datetime

    patient = Patient.query.get(current_user.id)
    today = datetime.date.today()

    # Cards statistics specific to this patient
    today_appts = (
        Appointment.query
        .filter(Appointment.patient_id == current_user.id, Appointment.appointment_date == today, Appointment.status != 'Cancelled')
        .count()
    )
    total_appts = (
        Appointment.query
        .filter(Appointment.patient_id == current_user.id)
        .count()
    )
    total_records = (
        MedicalRecord.query
        .filter_by(patient_id=current_user.id)
        .count()
    )

    my_appointments = (
        Appointment.query
        .filter_by(patient_id=current_user.id)
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        .all()
    )

    my_records = (
        MedicalRecord.query
        .filter_by(patient_id=current_user.id)
        .order_by(MedicalRecord.visit_date.desc())
        .limit(5)
        .all()
    )

    # Chart data: Patient's appointment status distribution
    status_counts = (
        db.session.query(Appointment.status, db.func.count(Appointment.id))
        .filter(Appointment.patient_id == current_user.id)
        .group_by(Appointment.status)
        .all()
    )
    status_chart = {s: c for s, c in status_counts}

    context = {
        'title':           'My Dashboard',
        'patient':         patient,
        'today_appts':     today_appts,
        'total_appts':     total_appts,
        'total_records':    total_records,
        'my_appointments': my_appointments,
        'my_records':      my_records,
        'status_chart':    status_chart
    }
    return render_template('dashboards/patient.html', **context)



@patient_bp.route('/')
@patient_bp.route('/list')
@login_required
@roles_required('Admin', 'Nurse', 'Doctor')
def list_patients_view():
    """Directory list of patients with search, sort, and pagination."""
    from services.patient_service import list_patients
    import math

    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'last_name')
    direction = request.args.get('direction', 'asc')

    per_page = 10
    patients, total = list_patients(
        page=page,
        per_page=per_page,
        sort_by=sort,
        sort_dir=direction,
        search_term=q if q else None
    )

    total_pages = math.ceil(total / per_page)

    context = {
        'title': 'Patient Directory',
        'patients': patients,
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'q': q,
        'sort': sort,
        'direction': direction
    }
    return render_template('patients/list.html', **context)


@patient_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Nurse')
def add_patient_view():
    """Register a new patient profile and associated user account."""
    from forms.patient_form import PatientForm
    from services.patient_service import create_patient
    from models.user import User

    form = PatientForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        # Verify email uniqueness
        if User.query.filter_by(email=email).first():
            form.email.errors.append('A user account with this email address already exists.')
            return render_template('patients/add_edit.html', form=form, title='Add Patient', action='add')

        create_patient(form.data)
        flash('Patient registered successfully!', 'success')
        return redirect(url_for('patient.list_patients_view'))

    return render_template('patients/add_edit.html', form=form, title='Add Patient', action='add')


@patient_bp.route('/edit/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Nurse', 'Patient')
def edit_patient_view(patient_id):
    """Edit patient demographics and update synced user details."""
    from forms.patient_form import PatientForm
    from services.patient_service import get_patient, update_patient
    from models.user import User

    if current_user.role.name == 'Patient' and current_user.id != patient_id:
        abort(403)

    patient = get_patient(patient_id)
    
    # Pre-populate form fields on GET
    if request.method == 'GET':
        form = PatientForm(obj=patient)
    else:
        form = PatientForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        # Check email uniqueness against other users
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != patient_id:
            form.email.errors.append('A user account with this email address already exists.')
            return render_template('patients/add_edit.html', form=form, title='Edit Patient', action='edit', patient=patient)

        update_patient(patient_id, form.data)
        flash('Patient profile updated successfully!', 'success')

        if current_user.role.name == 'Patient':
            return redirect(url_for('patient.dashboard'))
        return redirect(url_for('patient.view_patient_view', patient_id=patient_id))

    return render_template('patients/add_edit.html', form=form, title='Edit Patient', action='edit', patient=patient)


@patient_bp.route('/delete/<int:patient_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Nurse')
def delete_patient_view(patient_id):
    """Soft-delete a patient user account."""
    from services.patient_service import delete_patient
    delete_patient(patient_id)
    flash('Patient record soft-deleted successfully.', 'success')
    return redirect(url_for('patient.list_patients_view'))


@patient_bp.route('/view/<int:patient_id>')
@login_required
@roles_required('Admin', 'Nurse', 'Doctor', 'Patient')
def view_patient_view(patient_id):
    """View detailed demographics, medical records, and appointment history of a patient."""
    from services.patient_service import get_patient
    
    if current_user.role.name == 'Patient' and current_user.id != patient_id:
        abort(403)

    patient = get_patient(patient_id)

    # Fetch history
    appointments = (
        Appointment.query
        .filter_by(patient_id=patient_id)
        .order_by(Appointment.appointment_date.desc())
        .all()
    )

    medical_records = (
        MedicalRecord.query
        .filter_by(patient_id=patient_id)
        .order_by(MedicalRecord.visit_date.desc())
        .all()
    )

    context = {
        'title': f"Patient Profile — {patient.full_name}",
        'patient': patient,
        'appointments': appointments,
        'medical_records': medical_records
    }
    return render_template('patients/view.html', **context)
