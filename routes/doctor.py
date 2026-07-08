# =============================================================================
# routes/doctor.py — Doctor Blueprint
# =============================================================================
# URL prefix: /doctor  (set in app.py)
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps

from utils.decorators import role_required
from models.appointment import Appointment
from models.medical_record import MedicalRecord
from database.connection import db

doctor_bp = Blueprint('doctor', __name__)


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


@doctor_bp.route('/dashboard')
@login_required
@role_required('Doctor')
def dashboard():
    """Doctor home — upcoming appointments, statistics, and chart data."""
    from models.doctor import Doctor
    from models.medical_record import MedicalRecord
    import datetime

    doctor = Doctor.query.get(current_user.id)
    today = datetime.date.today()

    # Cards statistics specific to this doctor
    today_appts = (
        Appointment.query
        .filter(Appointment.doctor_id == current_user.id, Appointment.appointment_date == today, Appointment.status != 'Cancelled')
        .count()
    )
    upcoming_appts = (
        Appointment.query
        .filter(Appointment.doctor_id == current_user.id, Appointment.appointment_date > today, Appointment.status != 'Cancelled')
        .count()
    )
    total_patients = (
        db.session.query(db.func.count(db.distinct(Appointment.patient_id)))
        .filter(Appointment.doctor_id == current_user.id, Appointment.status != 'Cancelled')
        .scalar() or 0
    )

    # Lists
    upcoming_appointments = (
        Appointment.query
        .filter(Appointment.doctor_id == current_user.id, Appointment.appointment_date >= today, Appointment.status != 'Cancelled')
        .order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
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

    # Chart: Doctor's own appointment statuses
    status_counts = (
        db.session.query(Appointment.status, db.func.count(Appointment.id))
        .filter(Appointment.doctor_id == current_user.id)
        .group_by(Appointment.status)
        .all()
    )
    status_chart = {s: c for s, c in status_counts}

    context = {
        'title':                 'Doctor Dashboard',
        'doctor':                doctor,
        'today_appts':           today_appts,
        'upcoming_appts':        upcoming_appts,
        'total_patients':        total_patients,
        'upcoming_appointments': upcoming_appointments,
        'recent_records':        recent_records,
        'status_chart':          status_chart
    }
    return render_template('dashboards/doctor.html', **context)



@doctor_bp.route('/')
@doctor_bp.route('/list')
@login_required
@roles_required('Admin', 'Nurse', 'Doctor')
def list_doctors_view():
    """Directory list of doctors with search, sort, and pagination."""
    from services.doctor_service import list_doctors
    import math

    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'last_name')
    direction = request.args.get('direction', 'asc')

    per_page = 10
    doctors, total = list_doctors(
        page=page,
        per_page=per_page,
        sort_by=sort,
        sort_dir=direction,
        search_term=q if q else None
    )

    total_pages = math.ceil(total / per_page)

    context = {
        'title': 'Doctor Directory',
        'doctors': doctors,
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'q': q,
        'sort': sort,
        'direction': direction
    }
    return render_template('doctors/list.html', **context)


@doctor_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin')
def add_doctor_view():
    """Register a new doctor profile and associated user credentials account."""
    from forms.doctor_form import DoctorForm
    from services.doctor_service import create_doctor
    from models.department import Department
    from models.user import User

    form = DoctorForm()
    # Populate departments dropdown choices dynamically
    departments = Department.query.order_by(Department.name.asc()).all()
    form.department_id.choices = [(d.id, d.name) for d in departments]

    if form.validate_on_submit():
        email = form.email_address.data.lower().strip()
        # Verify email uniqueness
        if User.query.filter_by(email=email).first():
            form.email_address.errors.append('A user account with this email address already exists.')
            return render_template('doctors/add_edit.html', form=form, title='Add Doctor', action='add')

        create_doctor(form.data)
        flash('Doctor registered successfully!', 'success')
        return redirect(url_for('doctor.list_doctors_view'))

    return render_template('doctors/add_edit.html', form=form, title='Add Doctor', action='add')


@doctor_bp.route('/edit/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Doctor')
def edit_doctor_view(doctor_id):
    """Edit doctor demographics and availability schedule."""
    from forms.doctor_form import DoctorForm
    from services.doctor_service import get_doctor, update_doctor
    from models.department import Department
    from models.user import User

    if current_user.role.name == 'Doctor' and current_user.id != doctor_id:
        abort(403)

    doctor = get_doctor(doctor_id)
    
    # Pre-populate form fields on GET
    if request.method == 'GET':
        form = DoctorForm(obj=doctor)
    else:
        form = DoctorForm()
        
    departments = Department.query.order_by(Department.name.asc()).all()
    form.department_id.choices = [(d.id, d.name) for d in departments]

    if form.validate_on_submit():
        email = form.email_address.data.lower().strip()
        # Check email uniqueness against other users
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != doctor_id:
            form.email_address.errors.append('A user account with this email address already exists.')
            return render_template('doctors/add_edit.html', form=form, title='Edit Doctor', action='edit', doctor=doctor)

        update_doctor(doctor_id, form.data)
        flash('Doctor profile updated successfully!', 'success')

        if current_user.role.name == 'Doctor':
            return redirect(url_for('doctor.dashboard'))
        return redirect(url_for('doctor.view_doctor_view', doctor_id=doctor_id))

    return render_template('doctors/add_edit.html', form=form, title='Edit Doctor', action='edit', doctor=doctor)


@doctor_bp.route('/delete/<int:doctor_id>', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_doctor_view(doctor_id):
    """Soft-delete a doctor user account."""
    from services.doctor_service import delete_doctor
    delete_doctor(doctor_id)
    flash('Doctor profile soft-deleted successfully.', 'success')
    return redirect(url_for('doctor.list_doctors_view'))


@doctor_bp.route('/view/<int:doctor_id>')
@login_required
@roles_required('Admin', 'Nurse', 'Doctor', 'Patient')
def view_doctor_view(doctor_id):
    """View detailed demographics, consulting department, availability, and scheduling."""
    from services.doctor_service import get_doctor
    
    doctor = get_doctor(doctor_id)

    # Fetch doctor's upcoming appointments
    upcoming_appointments = (
        Appointment.query
        .filter_by(doctor_id=doctor_id)
        .order_by(Appointment.appointment_date.asc())
        .limit(10)
        .all()
    )

    context = {
        'title': f"Doctor Profile — Dr. {doctor.full_name}",
        'doctor': doctor,
        'upcoming_appointments': upcoming_appointments
    }
    return render_template('doctors/view.html', **context)
