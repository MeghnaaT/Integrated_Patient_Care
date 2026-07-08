# =============================================================================
# routes/nurse.py — Nurse Blueprint
# =============================================================================
# URL prefix: /nurse  (set in app.py)
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps

from utils.decorators import role_required
from models.patient import Patient
from models.appointment import Appointment
from models.user import User
from database.connection import db

nurse_bp = Blueprint('nurse', __name__)


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


@nurse_bp.route('/dashboard')
@login_required
@role_required('Nurse')
def dashboard():
    """Nurse home — active patient list, scheduling logs, statistics, and chart data."""
    from models.nurse import Nurse
    import datetime

    nurse = Nurse.query.get(current_user.id)
    today = datetime.date.today()

    # Cards statistics
    total_patients = Patient.query.join(User).filter(User.is_active.is_(True)).count()
    today_appts = Appointment.query.filter(Appointment.appointment_date == today, Appointment.status != 'Cancelled').count()
    upcoming_appts = Appointment.query.filter(Appointment.appointment_date > today, Appointment.status != 'Cancelled').count()

    all_patients = Patient.query.join(User).filter(User.is_active.is_(True)).order_by(Patient.last_name.asc()).all()

    today_appointments = (
        Appointment.query
        .filter(Appointment.appointment_date == today, Appointment.status != 'Cancelled')
        .order_by(Appointment.appointment_time.asc())
        .limit(20)
        .all()
    )

    # Chart data: Today's appointment status breakdown
    status_counts = (
        db.session.query(Appointment.status, db.func.count(Appointment.id))
        .filter(Appointment.appointment_date == today)
        .group_by(Appointment.status)
        .all()
    )
    status_chart = {s: c for s, c in status_counts}

    context = {
        'title':              'Nurse Dashboard',
        'nurse':              nurse,
        'today':              today,
        'total_patients':     total_patients,
        'today_appts':        today_appts,
        'upcoming_appts':     upcoming_appts,
        'all_patients':       all_patients,
        'today_appointments': today_appointments,
        'status_chart':       status_chart
    }
    return render_template('dashboards/nurse.html', **context)



@nurse_bp.route('/')
@nurse_bp.route('/list')
@login_required
@roles_required('Admin', 'Nurse', 'Doctor')
def list_nurses_view():
    """Directory list of nurses with search, sort, and pagination."""
    from services.nurse_service import list_nurses
    import math

    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'last_name')
    direction = request.args.get('direction', 'asc')

    per_page = 10
    nurses, total = list_nurses(
        page=page,
        per_page=per_page,
        sort_by=sort,
        sort_dir=direction,
        search_term=q if q else None
    )

    total_pages = math.ceil(total / per_page)

    context = {
        'title': 'Nurse Directory',
        'nurses': nurses,
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'q': q,
        'sort': sort,
        'direction': direction
    }
    return render_template('nurses/list.html', **context)


@nurse_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin')
def add_nurse_view():
    """Register a new nurse profile and associated user account."""
    from forms.nurse_form import NurseForm
    from services.nurse_service import create_nurse
    from models.department import Department
    from models.user import User

    form = NurseForm()
    # Populate departments dropdown choices dynamically
    departments = Department.query.order_by(Department.name.asc()).all()
    form.department_id.choices = [(d.id, d.name) for d in departments]

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        # Verify email uniqueness
        if User.query.filter_by(email=email).first():
            form.email.errors.append('A user account with this email address already exists.')
            return render_template('nurses/add_edit.html', form=form, title='Add Nurse', action='add')

        create_nurse(form.data)
        flash('Nurse registered successfully!', 'success')
        return redirect(url_for('nurse.list_nurses_view'))

    return render_template('nurses/add_edit.html', form=form, title='Add Nurse', action='add')


@nurse_bp.route('/edit/<int:nurse_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Nurse')
def edit_nurse_view(nurse_id):
    """Edit nurse details like shift or department."""
    from forms.nurse_form import NurseForm
    from services.nurse_service import get_nurse, update_nurse
    from models.department import Department
    from models.user import User

    if current_user.role.name == 'Nurse' and current_user.id != nurse_id:
        abort(403)

    nurse = get_nurse(nurse_id)
    
    # Pre-populate form fields on GET, sync email from User model
    if request.method == 'GET':
        form = NurseForm(obj=nurse)
        if nurse.user:
            form.email.data = nurse.user.email
    else:
        form = NurseForm()
        
    departments = Department.query.order_by(Department.name.asc()).all()
    form.department_id.choices = [(d.id, d.name) for d in departments]

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        # Check email uniqueness against other users
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != nurse_id:
            form.email.errors.append('A user account with this email address already exists.')
            return render_template('nurses/add_edit.html', form=form, title='Edit Nurse', action='edit', nurse=nurse)

        update_nurse(nurse_id, form.data)
        flash('Nurse profile updated successfully!', 'success')

        if current_user.role.name == 'Nurse':
            return redirect(url_for('nurse.dashboard'))
        return redirect(url_for('nurse.view_nurse_view', nurse_id=nurse_id))

    return render_template('nurses/add_edit.html', form=form, title='Edit Nurse', action='edit', nurse=nurse)


@nurse_bp.route('/delete/<int:nurse_id>', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_nurse_view(nurse_id):
    """Soft-delete a nurse user account."""
    from services.nurse_service import delete_nurse
    delete_nurse(nurse_id)
    flash('Nurse profile soft-deleted successfully.', 'success')
    return redirect(url_for('nurse.list_nurses_view'))


@nurse_bp.route('/view/<int:nurse_id>')
@login_required
@roles_required('Admin', 'Nurse', 'Doctor', 'Patient')
def view_nurse_view(nurse_id):
    """View detailed nurse demographics, shift, and department."""
    from services.nurse_service import get_nurse
    
    nurse = get_nurse(nurse_id)

    context = {
        'title': f"Nurse Profile — {nurse.full_name}",
        'nurse': nurse
    }
    return render_template('nurses/view.html', **context)
