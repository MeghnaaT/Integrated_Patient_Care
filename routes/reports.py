# =============================================================================
# routes/reports.py — Administrative Reports & Export Blueprint
# =============================================================================
# URL prefix: /reports
# =============================================================================

import datetime
from flask import Blueprint, render_template, request, redirect, url_for, abort, Response, flash
from flask_login import login_required, current_user
from utils.decorators import role_required

from database.connection import db
from models.appointment import Appointment
from models.patient import Patient
from models.doctor import Doctor
from models.department import Department
from services.report_export_service import fetch_report_data, generate_report_csv

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def view_reports():
    """Generates monthly reports split into weekly slots matching mockups."""
    today = datetime.date.today()
    
    report_type = request.args.get('report_type', '')
    selected_month = request.args.get('month', today.month, type=int)
    selected_year = request.args.get('year', today.year, type=int)

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
        start_date = datetime.date(selected_year, selected_month, 1)
        if selected_month == 12:
            end_date = datetime.date(selected_year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(selected_year, selected_month + 1, 1) - datetime.timedelta(days=1)

        weeks = [
            {"start": 1, "end": 7},
            {"start": 8, "end": 14},
            {"start": 15, "end": 21},
            {"start": 22, "end": end_date.day}
        ]

        if report_type == 'Monthly Appointment Report':
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


@reports_bp.route('/admin', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def admin_reports_hub():
    """Milestone 4 Day 2 Administrative Reports Dashboard with 12 report types, filters, search, pagination, and exports."""
    report_type = request.args.get('report_type', 'patient')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    doctor_id = request.args.get('doctor_id', type=int)
    department_id = request.args.get('department_id', type=int)
    status = request.args.get('status', '')
    search_query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    # Restrict Doctor & Nurse from accessing financial / executive admin reports
    admin_only_reports = {'billing', 'doctor_performance', 'department', 'monthly', 'pharmacy', 'notification'}
    if current_user.role.name in ['Doctor', 'Nurse'] and report_type in admin_only_reports:
        abort(403)

    if current_user.role.name == 'Doctor':
        doctor_id = current_user.id

    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

    report_result = fetch_report_data(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        doctor_id=doctor_id,
        department_id=department_id,
        status=status,
        search_query=search_query,
        page=page,
        per_page=15
    )

    doctors = Doctor.query.all()
    departments = Department.query.all()

    report_titles = {
        'patient': '1. Patient Report',
        'appointment': '2. Appointment Report',
        'consultation': '3. Consultation Report',
        'prescription': '4. Prescription Report',
        'doctor_performance': '5. Doctor Performance Report',
        'department': '6. Department-wise Report',
        'monthly': '7. Monthly Hospital Report',
        'billing': '8. Billing / Revenue Report',
        'laboratory': '9. Laboratory Report',
        'pharmacy': '10. Pharmacy Report',
        'notification': '11. Notification Report',
        'satisfaction': '12. Patient Satisfaction Report'
    }

    context = {
        'title': f"Administrative Reporting - {report_titles.get(report_type, 'Report')}",
        'report_type': report_type,
        'report_title': report_titles.get(report_type, 'Report'),
        'report_data': report_result,
        'doctors': doctors,
        'departments': departments,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'doctor_id': doctor_id,
        'department_id': department_id,
        'status': status,
        'search_query': search_query
    }
    return render_template('reports/admin_reports.html', **context)


@reports_bp.route('/export/csv', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def export_csv():
    """Export selected report as CSV file."""
    report_type = request.args.get('report_type', 'patient')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

    report_result = fetch_report_data(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        page=1,
        per_page=10000
    )

    csv_data = generate_report_csv(report_type, report_result)
    filename = f"IPCMS_{report_type}_report_{datetime.date.today()}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@reports_bp.route('/export/excel', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def export_excel():
    """Export selected report as Excel-compatible CSV file."""
    report_type = request.args.get('report_type', 'patient')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

    report_result = fetch_report_data(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        page=1,
        per_page=10000
    )

    csv_data = generate_report_csv(report_type, report_result)
    filename = f"IPCMS_{report_type}_report_{datetime.date.today()}.xls"

    return Response(
        csv_data,
        mimetype="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@reports_bp.route('/export/pdf', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def export_pdf():
    """Printable PDF view for report printing/downloading."""
    report_type = request.args.get('report_type', 'patient')
    report_result = fetch_report_data(
        report_type=report_type,
        page=1,
        per_page=1000
    )
    context = {
        'title': f"IPCMS Report - {report_type.replace('_', ' ').title()}",
        'report_type': report_type,
        'report_data': report_result,
        'today': datetime.date.today()
    }
    return render_template('reports/pdf_template.html', **context)


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
