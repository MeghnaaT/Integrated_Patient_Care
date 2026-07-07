# =============================================================================
# services/patient_service.py — Service layer for Patient Management
# =============================================================================
# Provides high‑level functions used by the Patient Blueprint. All database
# interactions are performed here so the route handlers stay thin and focused on
# request/response concerns.
# =============================================================================

from typing import List, Optional, Tuple

from database.connection import db
from models.patient import Patient
from models.medical_record import MedicalRecord

# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------

def create_patient(data: dict) -> Patient:
    """Create and persist a new Patient.

    ``data`` should contain keys matching the Patient model fields. The caller is
    responsible for validation (WTForms) before invoking this function.
    """
    patient = Patient(**data)
    db.session.add(patient)
    db.session.commit()
    return patient


def update_patient(patient_id: int, data: dict) -> Patient:
    """Update an existing patient with ``data`` and return the refreshed model."""
    patient = Patient.query.get_or_404(patient_id)
    for attr, value in data.items():
        setattr(patient, attr, value)
    db.session.commit()
    return patient


def delete_patient(patient_id: int) -> None:
    """Soft‑delete a patient by setting ``is_active`` to ``False``.

    A hard delete could be performed with ``db.session.delete`` but a soft delete
    preserves historical medical records while removing the patient from active
    lists.
    """
    patient = Patient.query.get_or_404(patient_id)
    patient.is_active = False
    db.session.commit()


def get_patient(patient_id: int) -> Patient:
    """Return a single patient (including lazy‑loaded relationships)."""
    return Patient.query.get_or_404(patient_id)

# ---------------------------------------------------------------------------
# List / Search / Pagination
# ---------------------------------------------------------------------------

def list_patients(
    page: int = 1,
    per_page: int = 10,
    sort_by: str = "last_name",
    sort_dir: str = "asc",
    search_term: Optional[str] = None,
) -> Tuple[List[Patient], int]:
    """Return a page of patients and the total count.

    * ``sort_by`` is limited to a whitelist of safe column names.
    * ``search_term`` performs a case‑insensitive LIKE on first_name, last_name,
      email and phone_number.
    """
    # Whitelist allowed sort columns to prevent SQL injection via ORM
    allowed_sorts = {"first_name", "last_name", "age", "created_on"}
    if sort_by not in allowed_sorts:
        sort_by = "last_name"
    order_clause = getattr(Patient, sort_by)
    if sort_dir.lower() == "desc":
        order_clause = order_clause.desc()
    else:
        order_clause = order_clause.asc()

    query = Patient.query.filter(Patient.is_active.is_(True))
    if search_term:
        like = f"%{search_term}%"
        query = query.filter(
            db.or_(Patient.first_name.ilike(like),
                   Patient.last_name.ilike(like),
                   Patient.email.ilike(like),
                   Patient.phone_number.ilike(like))
        )
    pagination = query.order_by(order_clause).paginate(page=page, per_page=per_page, error_out=False)
    return pagination.items, pagination.total

# ---------------------------------------------------------------------------
# Medical Record Helpers (for the Patient Profile page)
# ---------------------------------------------------------------------------

def add_medical_record(patient_id: int, record_data: dict) -> MedicalRecord:
    """Create a new MedicalRecord linked to ``patient_id``.

    ``record_data`` must contain the fields required by :class:`MedicalRecord`.
    """
    record = MedicalRecord(patient_id=patient_id, **record_data)
    db.session.add(record)
    db.session.commit()
    return record

def get_medical_records(patient_id: int, limit: int = 20) -> List[MedicalRecord]:
    """Return the most recent ``limit`` medical records for a patient."""
    return (
        MedicalRecord.query.filter_by(patient_id=patient_id)
        .order_by(MedicalRecord.visit_date.desc())
        .limit(limit)
        .all()
    )
