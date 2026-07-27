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


from utils.decorators import role_required


@reports_bp.route('/', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
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


@reports_bp.route('/search', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def patient_search():
    """Reports & Search module: search patient by ID or Name (matches Slide 43)."""
    from forms.search_form import PatientSearchForm
    from services.report_search_service import search_patients_by_id_or_name

    form = PatientSearchForm()
    patients = []
    found_patient = None

    query = request.args.get('query', '') or (form.query.data if request.method == 'POST' else '')
    search_by = request.args.get('search_by', 'patient_id') or (form.search_by.data if request.method == 'POST' else 'patient_id')

    if query:
        form.query.data = query
        form.search_by.data = search_by
        patients = search_patients_by_id_or_name(query, search_by)
        if patients:
            found_patient = patients[0]

    context = {
        'title': 'Reports & Search',
        'form': form,
        'patients': patients,
        'found_patient': found_patient,
        'query': query
    }
    return render_template('reports/patient_search.html', **context)


@reports_bp.route('/patient-report/<int:patient_id>', methods=['GET'])
@login_required
def generate_patient_report(patient_id: int):
    """Generate printable/downloadable comprehensive medical report for a patient."""
    from services.medical_history_service import get_complete_patient_history

    if current_user.role.name == 'Patient' and current_user.id != patient_id:
        abort(403)

    history = get_complete_patient_history(patient_id)
    context = {
        'title': f"Medical Report - {history['patient'].full_name}",
        'today': datetime.date.today(),
        **history
    }
    return render_template('reports/patient_report.html', **context)

