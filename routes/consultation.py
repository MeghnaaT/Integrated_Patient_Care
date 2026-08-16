# =============================================================================
# routes/consultation.py — Consultation Blueprint
# =============================================================================
# URL Prefix: /consultations
# =============================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
import datetime

from utils.decorators import role_required
from models.patient import Patient
from models.doctor import Doctor
from forms.consultation_form import ConsultationForm
from services.consultation_service import create_consultation, get_consultation_by_id, get_consultations_by_patient

consultation_bp = Blueprint('consultation', __name__)

def populate_choices(form):
    """Populate dynamic choices for Patient and Doctor fields."""
    from services.patient_service import get_doctor_associated_patient_ids
    if current_user.is_authenticated and current_user.role.name == 'Doctor':
        allowed_pids = get_doctor_associated_patient_ids(current_user.id)
        patients = Patient.query.filter(Patient.id.in_(list(allowed_pids) if allowed_pids else [-1])).all()
    else:
        patients = Patient.query.all()
    doctors = Doctor.query.all()
    form.patient_id.choices = [(p.id, f"{p.full_name} (PAT100{p.id} / ID:{p.id})") for p in patients]
    form.doctor_id.choices = [(d.id, f"Dr. {d.first_name} {d.last_name}") for d in doctors]

@consultation_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Doctor')
def add_consultation():
    """Add a new doctor consultation (matches Slide 15 mockup)."""
    from services.patient_service import get_doctor_associated_patient_ids
    form = ConsultationForm()
    populate_choices(form)

    # Default values
    if request.method == 'GET':
        patient_id_arg = request.args.get('patient_id', type=int)
        if patient_id_arg:
            form.patient_id.data = patient_id_arg
        if current_user.role.name == 'Doctor':
            form.doctor_id.data = current_user.id
        form.consultation_date.data = datetime.date.today()

    if request.method == 'POST' and current_user.role.name == 'Doctor':
        posted_pid = request.form.get('patient_id', type=int)
        if posted_pid:
            allowed_pids = get_doctor_associated_patient_ids(current_user.id)
            if posted_pid not in allowed_pids:
                abort(403)

    if form.validate_on_submit():
        if current_user.role.name == 'Doctor':
            allowed_pids = get_doctor_associated_patient_ids(current_user.id)
            if form.patient_id.data not in allowed_pids:
                abort(403)

        consultation = create_consultation(
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            consultation_date=form.consultation_date.data,
            symptoms=form.symptoms.data,
            diagnosis=form.diagnosis.data,
            treatment_notes=form.treatment_notes.data
        )
        flash('Consultation Details Saved Successfully!', 'success')
        return redirect(url_for('consultation.view_summary', id=consultation.id))

    context = {
        'title': 'Add Consultation',
        'form': form
    }
    return render_template('consultations/form.html', **context)

@consultation_bp.route('/summary/<int:id>', methods=['GET'])
@login_required
def view_summary(id: int):
    """Display Consultation Summary after submission (matches Slide 15 mockup)."""
    consultation = get_consultation_by_id(id)
    if not consultation:
        abort(404)

    # Role check for patients
    if current_user.role.name == 'Patient' and current_user.id != consultation.patient_id:
        abort(403)

    if current_user.role.name == 'Doctor' and current_user.id != consultation.doctor_id:
        from services.patient_service import get_doctor_associated_patient_ids
        allowed_pids = get_doctor_associated_patient_ids(current_user.id)
        if consultation.patient_id not in allowed_pids:
            abort(403)

    context = {
        'title': 'Consultation Summary',
        'consultation': consultation
    }
    return render_template('consultations/summary.html', **context)

@consultation_bp.route('/history/<int:patient_id>', methods=['GET'])
@login_required
def consultation_history(patient_id: int):
    """View consultation history list for a patient."""
    patient = Patient.query.get_or_404(patient_id)
    if current_user.role.name == 'Patient' and current_user.id != patient.id:
        abort(403)

    if current_user.role.name == 'Doctor':
        from services.patient_service import get_doctor_associated_patient_ids
        allowed_pids = get_doctor_associated_patient_ids(current_user.id)
        if patient_id not in allowed_pids:
            abort(403)

    consultations = get_consultations_by_patient(patient_id)
    context = {
        'title': f'Consultation History - {patient.full_name}',
        'patient': patient,
        'consultations': consultations
    }
    return render_template('consultations/history.html', **context)
