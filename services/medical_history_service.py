# =============================================================================
# services/medical_history_service.py — Patient Medical History Aggregator
# =============================================================================

from typing import Dict, Any
from models.patient import Patient
from services.ehr_service import get_or_create_ehr_detail, get_patient_allergies, get_patient_medications
from services.consultation_service import get_consultations_by_patient
from services.prescription_service import get_prescriptions_by_patient
from services.lab_service import get_lab_reports_by_patient

def get_complete_patient_history(patient_id: int) -> Dict[str, Any]:
    """
    Compile comprehensive, unified patient medical history including:
    - Demographic Details
    - EHR Vitals & Health Summary
    - Allergies & Active Medications
    - Consultation & Diagnosis History
    - Digital Prescriptions
    - Laboratory Test Reports
    """
    patient = Patient.query.get_or_404(patient_id)
    ehr = get_or_create_ehr_detail(patient_id)
    allergies = get_patient_allergies(patient_id)
    medications = get_patient_medications(patient_id)
    consultations = get_consultations_by_patient(patient_id)
    prescriptions = get_prescriptions_by_patient(patient_id)
    lab_reports = get_lab_reports_by_patient(patient_id)

    return {
        'patient': patient,
        'ehr': ehr,
        'allergies': allergies,
        'medications': medications,
        'consultations': consultations,
        'prescriptions': prescriptions,
        'lab_reports': lab_reports
    }
