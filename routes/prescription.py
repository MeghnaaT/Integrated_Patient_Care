# =============================================================================
# routes/prescription.py — Prescription Blueprint
# =============================================================================
# URL Prefix: /prescriptions
# =============================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
import datetime

from utils.decorators import role_required
from models.patient import Patient
from models.doctor import Doctor
from forms.prescription_form import PrescriptionForm
from services.prescription_service import create_prescription, get_prescription_by_id, get_prescriptions_by_patient, get_recent_prescriptions

prescription_bp = Blueprint('prescription', __name__)

def populate_choices(form):
    from services.patient_service import get_doctor_associated_patient_ids
    if current_user.is_authenticated and current_user.role.name == 'Doctor':
        allowed_pids = get_doctor_associated_patient_ids(current_user.id)
        patients = Patient.query.filter(Patient.id.in_(list(allowed_pids) if allowed_pids else [-1])).all()
    else:
        patients = Patient.query.all()
    doctors = Doctor.query.all()
    form.patient_id.choices = [(p.id, f"{p.full_name} (PAT100{p.id})") for p in patients]
    form.doctor_id.choices = [(d.id, f"Dr. {d.first_name} {d.last_name}") for d in doctors]

@prescription_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Doctor')
def add_prescription():
    """Create a digital prescription."""
    from services.patient_service import get_doctor_associated_patient_ids
    form = PrescriptionForm()
    populate_choices(form)

    if request.method == 'GET':
        patient_id_arg = request.args.get('patient_id', type=int)
        consultation_id_arg = request.args.get('consultation_id', type=int)
        if patient_id_arg:
            form.patient_id.data = patient_id_arg
        if current_user.role.name == 'Doctor':
            form.doctor_id.data = current_user.id
        form.prescription_date.data = datetime.date.today()

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

        items_data = [
            {
                'medicine_name': form.medicine_name_1.data,
                'dosage': form.dosage_1.data,
                'frequency': form.frequency_1.data,
                'duration': form.duration_1.data
            }
        ]
        if form.medicine_name_2.data:
            items_data.append({
                'medicine_name': form.medicine_name_2.data,
                'dosage': form.dosage_2.data,
                'frequency': form.frequency_2.data,
                'duration': form.duration_2.data
            })

        consultation_id_val = request.args.get('consultation_id', type=int)
        prescription = create_prescription(
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            prescription_date=form.prescription_date.data,
            special_instructions=form.special_instructions.data,
            items_data=items_data,
            consultation_id=consultation_id_val
        )
        flash('Digital Prescription Generated Successfully!', 'success')
        return redirect(url_for('prescription.view_prescription', id=prescription.id))

    context = {
        'title': 'Create Prescription',
        'form': form
    }
    return render_template('prescriptions/form.html', **context)

@prescription_bp.route('/view/<int:id>', methods=['GET'])
@login_required
def view_prescription(id: int):
    """View Digital Prescription Summary & Print ticket."""
    prescription = get_prescription_by_id(id)
    if not prescription:
        abort(404)

    if current_user.role.name == 'Patient' and current_user.id != prescription.patient_id:
        abort(403)

    if current_user.role.name == 'Doctor' and current_user.id != prescription.doctor_id:
        from services.patient_service import get_doctor_associated_patient_ids
        allowed_pids = get_doctor_associated_patient_ids(current_user.id)
        if prescription.patient_id not in allowed_pids:
            abort(403)

    context = {
        'title': f'Prescription #{prescription.id}',
        'prescription': prescription
    }
    return render_template('prescriptions/view.html', **context)

@prescription_bp.route('/list', methods=['GET'])
@login_required
def list_prescriptions():
    """List prescriptions depending on user role."""
    from models.prescription import Prescription
    if current_user.role.name == 'Patient':
        prescriptions = get_prescriptions_by_patient(current_user.id)
    elif current_user.role.name == 'Doctor':
        prescriptions = Prescription.query.filter_by(doctor_id=current_user.id).order_by(Prescription.prescription_date.desc()).all()
    else:
        prescriptions = get_recent_prescriptions(limit=50)

    context = {
        'title': 'Prescriptions Management',
        'prescriptions': prescriptions
    }
    return render_template('prescriptions/list.html', **context)
