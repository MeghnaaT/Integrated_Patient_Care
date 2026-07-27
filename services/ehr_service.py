# =============================================================================
# services/ehr_service.py — EHR Management Service Layer
# =============================================================================

from typing import Optional, List
from database.connection import db
from models.ehr_detail import EHRDetail, Allergy, PatientMedication
from models.patient import Patient

def get_or_create_ehr_detail(patient_id: int) -> EHRDetail:
    """Retrieve existing EHR detail for patient, or create a default one if not exists."""
    ehr = EHRDetail.query.filter_by(patient_id=patient_id).first()
    if not ehr:
        ehr = EHRDetail(patient_id=patient_id, height=170, weight=70, bmi=24.2, smoking_status='No', alcohol_status='No', chronic_diseases='No', remarks='Initial EHR setup.')
        db.session.add(ehr)
        db.session.commit()
    return ehr

def update_ehr_detail(patient_id: int, data: dict) -> EHRDetail:
    """Update vitals and health summary for a patient."""
    ehr = get_or_create_ehr_detail(patient_id)
    for key, val in data.items():
        if hasattr(ehr, key) and val is not None:
            setattr(ehr, key, val)
    db.session.commit()
    return ehr

def add_allergy(patient_id: int, allergen: str, reaction: str, added_on) -> Allergy:
    """Add a new allergy to a patient's record."""
    allergy = Allergy(patient_id=patient_id, allergen=allergen, reaction=reaction, added_on=added_on)
    db.session.add(allergy)
    db.session.commit()
    return allergy

def get_patient_allergies(patient_id: int) -> List[Allergy]:
    """Get all allergies for a patient."""
    return Allergy.query.filter_by(patient_id=patient_id).order_by(Allergy.added_on.desc()).all()

def add_patient_medication(patient_id: int, medicine: str, dosage: str, frequency: str, start_date) -> PatientMedication:
    """Add a current active medication for a patient."""
    med = PatientMedication(patient_id=patient_id, medicine=medicine, dosage=dosage, frequency=frequency, start_date=start_date)
    db.session.add(med)
    db.session.commit()
    return med

def get_patient_medications(patient_id: int) -> List[PatientMedication]:
    """Get all active medications for a patient."""
    return PatientMedication.query.filter_by(patient_id=patient_id).order_by(PatientMedication.start_date.desc()).all()
