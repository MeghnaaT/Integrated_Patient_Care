# =============================================================================
# routes/admin.py — Admin Blueprint
# =============================================================================
# URL prefix: /admin  (set in app.py)
# Requires:   role == 'Admin'
# =============================================================================

from flask import Blueprint, render_template
from flask_login import login_required
import datetime
from database.connection import db

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
    """Admin main dashboard — summary statistics, recent records, and chart data."""
    # Count active demographics only (where corresponding user is active)
    total_patients = Patient.query.join(User).filter(User.is_active.is_(True)).count()
    total_doctors  = Doctor.query.join(User).filter(User.is_active.is_(True)).count()
    total_nurses   = Nurse.query.join(User).filter(User.is_active.is_(True)).count()
    total_appts    = Appointment.query.count()

    # Today's & Upcoming Appointments
    today = datetime.date.today()
    today_appts = Appointment.query.filter(Appointment.appointment_date == today, Appointment.status != 'Cancelled').count()
    upcoming_appts = Appointment.query.filter(Appointment.appointment_date > today, Appointment.status != 'Cancelled').count()

    # Recent Patients (last 5 added)
    recent_patients = (
        Patient.query
        .join(User)
        .filter(User.is_active.is_(True))
        .order_by(User.created_at.desc())
        .limit(5)
        .all()
    )

    # Recent Appointments (last 5 scheduled)
    recent_appointments = (
        Appointment.query
        .order_by(Appointment.created_at.desc())
        .limit(5)
        .all()
    )

    # Chart 1: Appointment Status Distribution
    status_counts = (
        db.session.query(Appointment.status, db.func.count(Appointment.id))
        .group_by(Appointment.status)
        .all()
    )
    status_chart = {s: c for s, c in status_counts}

    # Chart 2: Patient Gender Distribution
    gender_counts = (
        db.session.query(Patient.gender, db.func.count(Patient.id))
        .join(User)
        .filter(User.is_active.is_(True))
        .group_by(Patient.gender)
        .all()
    )
    gender_chart = {g: c for g, c in gender_counts}

    context = {
        'title':               'Admin Dashboard',
        'total_patients':      total_patients,
        'total_doctors':       total_doctors,
        'total_nurses':        total_nurses,
        'total_appts':         total_appts,
        'today_appts':         today_appts,
        'upcoming_appts':      upcoming_appts,
        'recent_patients':     recent_patients,
        'recent_appointments': recent_appointments,
        'status_chart':        status_chart,
        'gender_chart':        gender_chart
    }
    return render_template('dashboards/admin.html', **context)

