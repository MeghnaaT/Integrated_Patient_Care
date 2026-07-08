# =============================================================================
# routes/reports.py — Reports Blueprint
# =============================================================================
# URL prefix: /reports
# =============================================================================

import datetime
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user

from database.connection import db
from models.appointment import Appointment
from models.patient import Patient

reports_bp = Blueprint('reports', __name__)


def roles_required(*role_names: str):
    """Enforces specific role mappings for reports access."""
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


@reports_bp.route('/', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def view_reports():
    """Generates monthly reports split into weekly slots matching mockups."""
    today = datetime.date.today()
    
    # Read selection inputs from query parameters
    report_type = request.args.get('report_type', '')
    selected_month = request.args.get('month', today.month, type=int)
    selected_year = request.args.get('year', today.year, type=int)

    # Static data lists for dropdown builders
    months_list = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December")
    ]
    years_list = [2024, 2025, 2026, 2027, 2028]

    report_data = []
    total_count = 0
    show_results = False

    if report_type:
        show_results = True
        
        # Calculate date boundaries for the selected month/year
        start_date = datetime.date(selected_year, selected_month, 1)
        if selected_month == 12:
            end_date = datetime.date(selected_year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(selected_year, selected_month + 1, 1) - datetime.timedelta(days=1)

        # 4 weeks grouping ranges
        weeks = [
            {"start": 1, "end": 7},
            {"start": 8, "end": 14},
            {"start": 15, "end": 21},
            {"start": 22, "end": end_date.day}
        ]

        if report_type == 'Monthly Appointment Report':
            # Fetch all appointments in range
            appointments = (
                Appointment.query
                .filter(Appointment.appointment_date >= start_date, Appointment.appointment_date <= end_date)
                .all()
            )
            for w in weeks:
                w_start = datetime.date(selected_year, selected_month, w["start"])
                w_end = datetime.date(selected_year, selected_month, w["end"])
                count = sum(1 for a in appointments if w_start <= a.appointment_date <= w_end)
                range_str = f"{w['start']:02d}-{selected_month:02d}-{selected_year} to {w['end']:02d}-{selected_month:02d}-{selected_year}"
                report_data.append({
                    "range": range_str,
                    "count": count
                })
                total_count += count

        elif report_type == 'Patient Registration Report':
            # Fetch all patients registered in range
            patients = (
                Patient.query
                .filter(Patient.registered_on >= start_date, Patient.registered_on <= end_date)
                .all()
            )
            for w in weeks:
                w_start = datetime.date(selected_year, selected_month, w["start"])
                w_end = datetime.date(selected_year, selected_month, w["end"])
                count = sum(1 for p in patients if w_start <= p.registered_on <= w_end)
                range_str = f"{w['start']:02d}-{selected_month:02d}-{selected_year} to {w['end']:02d}-{selected_month:02d}-{selected_year}"
                report_data.append({
                    "range": range_str,
                    "count": count
                })
                total_count += count

    context = {
        "title": "Reports",
        "report_type": report_type,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "months_list": months_list,
        "years_list": years_list,
        "report_data": report_data,
        "total_count": total_count,
        "show_results": show_results,
        "month_name": dict(months_list).get(selected_month, "")
    }

    return render_template('reports/view.html', **context)
