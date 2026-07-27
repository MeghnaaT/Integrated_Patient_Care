# =============================================================================
# routes/lab.py — Laboratory Blueprint
# =============================================================================
# URL Prefix: /laboratory
# =============================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
import datetime

from utils.decorators import role_required
from models.patient import Patient
from models.doctor import Doctor
from forms.lab_report_form import LabReportForm
from services.lab_service import create_lab_report, get_lab_report_by_id, get_lab_reports_by_patient, get_recent_lab_reports

laboratory_bp = Blueprint('laboratory', __name__)

def populate_choices(form):
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    form.patient_id.choices = [(p.id, f"{p.full_name} (PAT100{p.id})") for p in patients]
    form.doctor_id.choices = [(d.id, f"Dr. {d.first_name} {d.last_name}") for d in doctors]

@laboratory_bp.route('/request', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def request_lab_report():
    """Lab test request & result entry form."""
    form = LabReportForm()
    populate_choices(form)

    if request.method == 'GET':
        patient_id_arg = request.args.get('patient_id', type=int)
        if patient_id_arg:
            form.patient_id.data = patient_id_arg
        if current_user.role.name == 'Doctor':
            form.doctor_id.data = current_user.id
        form.test_date.data = datetime.date.today()

    if form.validate_on_submit():
        report = create_lab_report(
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            test_name=form.test_name.data,
            test_date=form.test_date.data,
            result=form.result.data,
            remarks=form.remarks.data
        )
        flash('Laboratory Report Saved Successfully!', 'success')
        return redirect(url_for('laboratory.view_report', id=report.id))

    context = {
        'title': 'Add Laboratory Test Report',
        'form': form
    }
    return render_template('laboratory/request_form.html', **context)

@laboratory_bp.route('/view/<int:id>', methods=['GET'])
@login_required
def view_report(id: int):
    """View detailed laboratory report."""
    report = get_lab_report_by_id(id)
    if not report:
        abort(404)

    if current_user.role.name == 'Patient' and current_user.id != report.patient_id:
        abort(403)

    context = {
        'title': f'Lab Report - {report.test_name}',
        'report': report
    }
    return render_template('laboratory/report_summary.html', **context)

@laboratory_bp.route('/reports', methods=['GET'])
@login_required
def list_reports():
    """List lab reports."""
    if current_user.role.name == 'Patient':
        reports = get_lab_reports_by_patient(current_user.id)
    else:
        reports = get_recent_lab_reports(limit=50)

    context = {
        'title': 'Laboratory Management',
        'reports': reports
    }
    return render_template('laboratory/list.html', **context)
