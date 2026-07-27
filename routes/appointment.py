# =============================================================================
# routes/appointment.py — Appointment Blueprint
# =============================================================================
# URL prefix: /appointment
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
import datetime

from models.appointment import Appointment
from models.doctor import Doctor
from models.patient import Patient
from forms.appointment_form import AppointmentForm
from database.connection import db

appointment_bp = Blueprint('appointment', __name__)


from utils.decorators import role_required


@appointment_bp.route('/')
@appointment_bp.route('/list')
@login_required
@role_required('Admin', 'Nurse', 'Doctor')
def list_appointments_view():
    """Directory list of appointments with filters, search, and pagination."""
    from services.appointment_service import list_appointments
    import math

    page = request.args.get('page', 1, type=int)
    doctor_id = request.args.get('doctor_id', type=int)
    patient_id = request.args.get('patient_id', type=int)
    status = request.args.get('status', '').strip()
    date_str = request.args.get('date', '').strip()

    filters = {}
    if doctor_id:
        filters['doctor_id'] = doctor_id
    if patient_id:
        filters['patient_id'] = patient_id
    if status:
        filters['status'] = status
    if date_str:
        try:
            filters['date'] = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    per_page = 10
    appts, total = list_appointments(
        page=page,
        per_page=per_page,
        filters=filters
    )

    total_pages = math.ceil(total / per_page)
    doctors = Doctor.query.order_by(Doctor.last_name.asc()).all()
    patients = Patient.query.order_by(Patient.last_name.asc()).all()

    context = {
        'title': 'Appointment Directory',
        'appointments': appts,
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'doctor_id': doctor_id,
        'patient_id': patient_id,
        'status': status,
        'date_str': date_str,
        'doctors': doctors,
        'patients': patients
    }
    return render_template('appointments/list.html', **context)


@appointment_bp.route('/book', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Nurse', 'Patient')
def book_appointment_view():
    """Book a new appointment."""
    from services.appointment_service import book_appointment

    form = AppointmentForm()
    
    # 1. Populate doctor choices
    doctors = Doctor.query.order_by(Doctor.last_name.asc()).all()
    form.doctor_id.choices = [(d.id, f"Dr. {d.full_name} ({d.specialization})") for d in doctors]

    # 2. Populate patient choices or default for current user
    if current_user.role.name in ['Admin', 'Nurse']:
        patients = Patient.query.order_by(Patient.last_name.asc()).all()
        form.patient_id.choices = [(p.id, p.full_name) for p in patients]
    else:
        # Patient is booking for themselves
        form.patient_id.choices = [(current_user.id, current_user.username)]
        # Make field optional and ignore input
        form.patient_id.validators = []

    if form.validate_on_submit():
        # Override patient_id to current_user if Patient role
        data = form.data
        if current_user.role.name == 'Patient':
            data['patient_id'] = current_user.id
            data['status'] = 'Pending'  # Self bookings default to Pending
        else:
            data['status'] = form.status.data or 'Confirmed'  # Staff bookings default to Confirmed

        appt, err = book_appointment(data)
        if not appt:
            flash(err, 'danger')
        else:
            flash('Appointment scheduled successfully!', 'success')
            if current_user.role.name == 'Patient':
                return redirect(url_for('patient.dashboard'))
            return redirect(url_for('appointment.list_appointments_view'))

    # Set default date to today
    if request.method == 'GET':
        form.appointment_date.data = datetime.date.today()

    return render_template('appointments/book_edit.html', form=form, title='Book Appointment', action='book')


@appointment_bp.route('/edit/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Nurse')
def edit_appointment_view(appointment_id):
    """Reschedule or update status of an appointment."""
    from services.appointment_service import get_appointment, update_appointment

    appt = get_appointment(appointment_id)
    form = AppointmentForm(obj=appt)

    # Populate choices
    doctors = Doctor.query.order_by(Doctor.last_name.asc()).all()
    form.doctor_id.choices = [(d.id, f"Dr. {d.full_name} ({d.specialization})") for d in doctors]

    patients = Patient.query.order_by(Patient.last_name.asc()).all()
    form.patient_id.choices = [(p.id, p.full_name) for p in patients]

    if form.validate_on_submit():
        res, err = update_appointment(appointment_id, form.data)
        if not res:
            flash(err, 'danger')
        else:
            flash('Appointment details modified successfully.', 'success')
            return redirect(url_for('appointment.list_appointments_view'))

    return render_template('appointments/book_edit.html', form=form, title='Reschedule Appointment', action='edit', appointment=appt)


@appointment_bp.route('/cancel/<int:appointment_id>', methods=['POST'])
@login_required
@role_required('Admin', 'Nurse', 'Patient')
def cancel_appointment_view(appointment_id):
    """Cancel an appointment."""
    from services.appointment_service import get_appointment, cancel_appointment

    appt = get_appointment(appointment_id)
    # Check permissions (Patients can only cancel their own)
    if current_user.role.name == 'Patient' and appt.patient_id != current_user.id:
        abort(403)

    cancel_appointment(appointment_id)
    flash('Appointment was cancelled successfully.', 'warning')
    
    if current_user.role.name == 'Patient':
        return redirect(url_for('patient.dashboard'))
    return redirect(url_for('appointment.list_appointments_view'))


@appointment_bp.route('/doctor/<int:doctor_id>/schedule')
@login_required
@role_required('Admin', 'Nurse', 'Doctor')
def doctor_schedule_view(doctor_id):
    """View the daily timetable schedule for a consulting doctor."""
    date_str = request.args.get('date', '').strip()
    if date_str:
        try:
            target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.date.today()
    else:
        target_date = datetime.date.today()

    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Query appointments chronologically
    appts = (
        Appointment.query
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == target_date,
            Appointment.status != 'Cancelled'
        )
        .order_by(Appointment.appointment_time.asc())
        .all()
    )

    context = {
        'title': f"Schedule — Dr. {doctor.full_name}",
        'doctor': doctor,
        'appointments': appts,
        'target_date': target_date,
        'date_str': target_date.strftime('%Y-%m-%d')
    }
    return render_template('appointments/doctor_schedule.html', **context)
