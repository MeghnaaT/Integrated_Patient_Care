# =============================================================================
# routes/ehr.py — EHR Blueprint
# =============================================================================
# URL Prefix: /ehr
# =============================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
import datetime

from utils.decorators import role_required
from models.patient import Patient
from forms.ehr_forms import EHRDetailForm, AllergyForm, PatientMedicationForm
from services.ehr_service import get_or_create_ehr_detail, update_ehr_detail, add_allergy, add_patient_medication, get_patient_allergies, get_patient_medications
from services.consultation_service import get_consultations_by_patient
from services.lab_service import get_lab_reports_by_patient

ehr_bp = Blueprint('ehr', __name__)

@ehr_bp.route('/<int:patient_id>', methods=['GET'])
@login_required
def view_ehr(patient_id: int):
    """Display Electronic Health Record dashboard for a patient (matches Slide 6)."""
    # Patients can only view their own EHR
    if current_user.role.name == 'Patient' and current_user.id != patient_id:
        abort(403)

    if current_user.role.name == 'Doctor':
        from services.patient_service import get_doctor_associated_patient_ids
        allowed_pids = get_doctor_associated_patient_ids(current_user.id)
        if patient_id not in allowed_pids:
            abort(403)

    patient = Patient.query.get_or_404(patient_id)

    ehr = get_or_create_ehr_detail(patient.id)
    allergies = get_patient_allergies(patient.id)
    medications = get_patient_medications(patient.id)
    consultations = get_consultations_by_patient(patient.id)
    lab_reports = get_lab_reports_by_patient(patient.id)

    allergy_form = AllergyForm(added_on=datetime.date.today())
    med_form = PatientMedicationForm(start_date=datetime.date.today())

    context = {
        'title': f'EHR - {patient.full_name}',
        'patient': patient,
        'ehr': ehr,
        'allergies': allergies,
        'medications': medications,
        'consultations': consultations,
        'lab_reports': lab_reports,
        'allergy_form': allergy_form,
        'med_form': med_form
    }
    return render_template('ehr/view.html', **context)

@ehr_bp.route('/edit/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def edit_ehr(patient_id: int):
    """Edit patient vitals and health summary."""
    if current_user.role.name == 'Doctor':
        from services.patient_service import get_doctor_associated_patient_ids
        allowed_pids = get_doctor_associated_patient_ids(current_user.id)
        if patient_id not in allowed_pids:
            abort(403)

    patient = Patient.query.get_or_404(patient_id)
    ehr = get_or_create_ehr_detail(patient.id)
    form = EHRDetailForm(obj=ehr)

    if form.validate_on_submit():
        data = {
            'height': form.height.data,
            'weight': form.weight.data,
            'bmi': form.bmi.data,
            'smoking_status': form.smoking_status.data,
            'alcohol_status': form.alcohol_status.data,
            'chronic_diseases': form.chronic_diseases.data,
            'remarks': form.remarks.data
        }
        update_ehr_detail(patient.id, data)
        flash('EHR Vitals updated successfully!', 'success')
        return redirect(url_for('ehr.view_ehr', patient_id=patient.id))

    return render_template('ehr/edit.html', title='Edit EHR Vitals', form=form, patient=patient)

@ehr_bp.route('/allergy/add/<int:patient_id>', methods=['POST'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def add_allergy_route(patient_id: int):
    """Add a new allergy entry."""
    form = AllergyForm()
    if form.validate_on_submit():
        add_allergy(patient_id, form.allergen.data, form.reaction.data, form.added_on.data)
        flash(f'Allergy "{form.allergen.data}" added successfully!', 'success')
    else:
        flash('Failed to add allergy. Please check form inputs.', 'danger')
    return redirect(url_for('ehr.view_ehr', patient_id=patient_id))

@ehr_bp.route('/medication/add/<int:patient_id>', methods=['POST'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def add_medication_route(patient_id: int):
    """Add an active medication entry."""
    form = PatientMedicationForm()
    if form.validate_on_submit():
        add_patient_medication(patient_id, form.medicine.data, form.dosage.data, form.frequency.data, form.start_date.data)
        flash(f'Medication "{form.medicine.data}" added successfully!', 'success')
    else:
        flash('Failed to add medication. Please check form inputs.', 'danger')
    return redirect(url_for('ehr.view_ehr', patient_id=patient_id))
