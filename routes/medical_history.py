# =============================================================================
# routes/medical_history.py — Patient Medical History Blueprint
# =============================================================================
# URL Prefix: /medical-history
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user

from models.patient import Patient
from forms.search_form import PatientSearchForm
from services.medical_history_service import get_complete_patient_history
from services.report_search_service import search_patients_by_id_or_name

medical_history_bp = Blueprint('medical_history', __name__)

@medical_history_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Medical history patient search & selection page (matches Slide 36/37)."""
    form = PatientSearchForm()
    patients = []

    # Patients automatically get redirected to their own medical history
    if current_user.role.name == 'Patient':
        return redirect(url_for('medical_history.view_patient_history', patient_id=current_user.id))

    if request.method == 'POST' and form.validate():
        patients = search_patients_by_id_or_name(form.query.data, form.search_by.data)
    else:
        query_arg = request.args.get('query', '')
        if query_arg:
            form.query.data = query_arg
            patients = search_patients_by_id_or_name(query_arg)
        else:
            patients = Patient.query.all()

    context = {
        'title': 'Patient Medical History Search',
        'form': form,
        'patients': patients
    }
    return render_template('medical_history/search.html', **context)

@medical_history_bp.route('/patient/<int:patient_id>', methods=['GET'])
@login_required
def view_patient_history(patient_id: int):
    """View complete unified medical history dashboard for a patient."""
    if current_user.role.name == 'Patient' and current_user.id != patient_id:
        abort(403)

    history = get_complete_patient_history(patient_id)
    context = {
        'title': f"Medical History - {history['patient'].full_name}",
        **history
    }
    return render_template('medical_history/view.html', **context)
