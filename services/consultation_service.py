# =============================================================================
# services/consultation_service.py — Consultation Service Layer
# =============================================================================

from typing import List, Optional
from database.connection import db
from models.consultation import Consultation
from models.patient import Patient
from models.doctor import Doctor

def create_consultation(patient_id: int, doctor_id: int, consultation_date, symptoms: str, diagnosis: str, treatment_notes: str) -> Consultation:
    """Create and persist a doctor consultation record."""
    consultation = Consultation(
        patient_id=patient_id,
        doctor_id=doctor_id,
        consultation_date=consultation_date,
        symptoms=symptoms,
        diagnosis=diagnosis,
        treatment_notes=treatment_notes
    )
    db.session.add(consultation)
    db.session.commit()
    return consultation

def get_consultation_by_id(consultation_id: int) -> Optional[Consultation]:
    """Retrieve consultation by ID."""
    return Consultation.query.get(consultation_id)

def get_consultations_by_patient(patient_id: int) -> List[Consultation]:
    """Get all consultations for a patient, ordered by date descending."""
    return Consultation.query.filter_by(patient_id=patient_id).order_by(Consultation.consultation_date.desc()).all()

def get_recent_consultations(limit: int = 10) -> List[Consultation]:
    """Get most recent consultations across the hospital."""
    return Consultation.query.order_by(Consultation.created_at.desc()).limit(limit).all()
