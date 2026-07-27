# =============================================================================
# services/prescription_service.py — Prescription Service Layer
# =============================================================================

from typing import List, Optional, Dict
from database.connection import db
from models.prescription import Prescription, PrescriptionItem

def create_prescription(patient_id: int, doctor_id: int, prescription_date, special_instructions: str, items_data: List[dict], consultation_id: Optional[int] = None) -> Prescription:
    """Create a digital prescription with multiple medicine items."""
    prescription = Prescription(
        patient_id=patient_id,
        doctor_id=doctor_id,
        consultation_id=consultation_id,
        prescription_date=prescription_date,
        special_instructions=special_instructions
    )
    db.session.add(prescription)
    db.session.flush() # Populate prescription.id

    for item in items_data:
        if item.get('medicine_name'):
            p_item = PrescriptionItem(
                prescription_id=prescription.id,
                medicine_name=item['medicine_name'],
                dosage=item.get('dosage', ''),
                frequency=item.get('frequency', ''),
                duration=item.get('duration', '')
            )
            db.session.add(p_item)

    db.session.commit()
    return prescription

def get_prescription_by_id(prescription_id: int) -> Optional[Prescription]:
    """Retrieve prescription by ID."""
    return Prescription.query.get(prescription_id)

def get_prescriptions_by_patient(patient_id: int) -> List[Prescription]:
    """Get all prescriptions for a patient."""
    return Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.prescription_date.desc()).all()

def get_recent_prescriptions(limit: int = 10) -> List[Prescription]:
    """Get recent prescriptions across the hospital."""
    return Prescription.query.order_by(Prescription.created_at.desc()).limit(limit).all()
