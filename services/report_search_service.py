# =============================================================================
# services/report_search_service.py — Search & Reports Service Layer
# =============================================================================

from typing import List, Optional
from database.connection import db
from models.patient import Patient

def search_patients_by_id_or_name(query: str, search_by: str = 'patient_id') -> List[Patient]:
    """
    Search for patients by Patient ID (e.g. 4 or PAT1001) or by First/Last Name.
    """
    if not query:
        return Patient.query.limit(20).all()

    query_str = query.strip()
    
    # Handle Patient ID search (support 'PAT1001' format by stripping 'PAT')
    if search_by == 'patient_id' or query_str.upper().startswith('PAT'):
        digits = ''.join(filter(str.isdigit, query_str))
        if digits:
            p_id = int(digits)
            if p_id > 1000:
                p_id -= 1000 # PAT1001 -> 1, or PAT4 -> 4 if formatted
            p = Patient.query.filter((Patient.id == p_id) | (Patient.id == int(digits))).all()
            if p:
                return p

    # Fallback to name/phone search
    like_term = f"%{query_str}%"
    return Patient.query.filter(
        db.or_(
            Patient.first_name.ilike(like_term),
            Patient.last_name.ilike(like_term),
            Patient.phone_number.ilike(like_term),
            Patient.email.ilike(like_term)
        )
    ).all()
