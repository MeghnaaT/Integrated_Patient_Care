# =============================================================================
# routes/feedback.py — Patient Feedback & Satisfaction Blueprint
# =============================================================================

import csv
import io
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort
from flask_login import login_required, current_user
from utils.decorators import role_required

from models.doctor import Doctor
from models.department import Department
from models.patient import Patient
from models.feedback import Feedback
from forms.feedback_form import FeedbackForm
from services.feedback_service import (
    create_feedback,
    can_patient_submit_feedback,
    get_patient_feedback_history,
    get_all_feedback,
    get_feedback_satisfaction_statistics
)

feedback_bp = Blueprint('feedback', __name__)

def populate_feedback_choices(form):
    """Populates dynamic doctor and department dropdown choices."""
    doctors = Doctor.query.order_by(Doctor.last_name.asc()).all()
    form.doctor_id.choices = [(0, '-- None / General --')] + [(d.id, f"Dr. {d.first_name} {d.last_name} ({d.specialization})") for d in doctors]
    
    departments = Department.query.order_by(Department.name.asc()).all()
    form.department_id.choices = [(0, '-- None / General --')] + [(dept.id, dept.name) for dept in departments]

@feedback_bp.route('/submit', methods=['GET', 'POST'])
@login_required
@role_required('Patient', 'Admin')
def submit_feedback():
    """Feedback submission page with star rating UI."""
    form = FeedbackForm()
    populate_feedback_choices(form)

    # Determine patient ID
    patient_id = current_user.id if current_user.role.name == 'Patient' else request.args.get('patient_id', current_user.id, type=int)

    if request.method == 'GET':
        consultation_id_arg = request.args.get('consultation_id', type=int)
        doctor_id_arg = request.args.get('doctor_id', type=int)
        if consultation_id_arg:
            form.consultation_id.data = str(consultation_id_arg)
        if doctor_id_arg:
            form.doctor_id.data = doctor_id_arg

    if form.validate_on_submit():
        try:
            doc_id = form.doctor_id.data if form.doctor_id.data and form.doctor_id.data > 0 else None
            dept_id = form.department_id.data if form.department_id.data and form.department_id.data > 0 else None
            consult_id = int(form.consultation_id.data) if form.consultation_id.data and form.consultation_id.data.isdigit() else None

            data = {
                'patient_id': patient_id,
                'doctor_id': doc_id,
                'department_id': dept_id,
                'consultation_id': consult_id,
                'service_type': form.service_type.data,
                'rating': form.rating.data,
                'comment': form.comment.data
            }

            fbk = create_feedback(data)
            flash(f"Thank you! Your feedback ({fbk.feedback_code}) has been submitted successfully.", "success")
            if current_user.role.name == 'Patient':
                return redirect(url_for('feedback.my_feedback'))
            return redirect(url_for('feedback.admin_feedback'))
        except ValueError as ve:
            flash(str(ve), "danger")

    return render_template('feedback/submit.html', form=form, title='Submit Patient Feedback')


@feedback_bp.route('/my-feedback', methods=['GET'])
@login_required
@role_required('Patient')
def my_feedback():
    """Patient's own submitted feedback history."""
    feedbacks = get_patient_feedback_history(current_user.id)
    return render_template('feedback/patient_history.html', feedbacks=feedbacks, title='My Submitted Feedback')


@feedback_bp.route('/admin', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def admin_feedback():
    """Administrator Feedback & Satisfaction Dashboard."""
    page = request.args.get('page', 1, type=int)
    service_type = request.args.get('service_type', '').strip()
    rating = request.args.get('rating', type=int)
    doctor_id = request.args.get('doctor_id', type=int)
    department_id = request.args.get('department_id', type=int)

    filters = {}
    if service_type:
        filters['service_type'] = service_type
    if rating:
        filters['rating'] = rating
    if doctor_id:
        filters['doctor_id'] = doctor_id
    if department_id:
        filters['department_id'] = department_id

    feedbacks, total = get_all_feedback(filters=filters, page=page, per_page=10)
    stats = get_feedback_satisfaction_statistics()
    doctors = Doctor.query.order_by(Doctor.last_name.asc()).all()
    departments = Department.query.order_by(Department.name.asc()).all()

    import math
    total_pages = math.ceil(total / 10)

    context = {
        'title': 'Patient Feedback & Satisfaction Dashboard',
        'feedbacks': feedbacks,
        'stats': stats,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'service_type': service_type,
        'rating': rating,
        'doctor_id': doctor_id,
        'department_id': department_id,
        'doctors': doctors,
        'departments': departments
    }
    return render_template('feedback/admin_feedback.html', **context)


@feedback_bp.route('/status/<int:id>', methods=['POST'])
@login_required
@role_required('Admin')
def update_status(id: int):
    """Allows Admin to mark feedback status as Reviewed or Published."""
    fbk = Feedback.query.get_or_404(id)
    new_status = request.form.get('status', 'Reviewed')
    if new_status in ['Published', 'Pending', 'Reviewed']:
        fbk.status = new_status
        from database.connection import db
        db.session.commit()
        flash(f"Feedback {fbk.feedback_code} status updated to {new_status}.", "success")
    return redirect(url_for('feedback.admin_feedback'))


@feedback_bp.route('/export/csv', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def export_csv():
    """Exports patient feedback data as CSV file attachment."""
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Feedback Code', 'Date', 'Patient Name', 'Category', 'Rating (1-5)', 'Doctor', 'Department', 'Comment', 'Status'])

    for f in feedbacks:
        doc_name = f"Dr. {f.doctor.full_name}" if f.doctor else 'N/A'
        dept_name = f.department.name if f.department else 'N/A'
        writer.writerow([
            f.feedback_code,
            f.created_date.strftime('%Y-%m-%d'),
            f.patient.full_name if f.patient else 'Anonymous',
            f.service_type,
            f.rating,
            doc_name,
            dept_name,
            f.comment or '',
            f.status
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=Patient_Satisfaction_Report_{datetime.date.today().strftime('%Y%m%d')}.csv"}
    )


@feedback_bp.route('/export/pdf', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def export_pdf():
    """Printable PDF feedback summary view."""
    stats = get_feedback_satisfaction_statistics()
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).limit(100).all()
    return render_template('reports/pdf_template.html', report_name='Patient Satisfaction Report', rows=feedbacks, stats=stats)
