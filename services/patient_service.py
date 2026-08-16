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
    """Create and persist a new Patient along with their User credential account.

    ``data`` should contain keys matching the Patient model fields. The caller is
    responsible for validation (WTForms) before invoking this function.
    """
    from models.user import User
    from models.role import Role
    from werkzeug.security import generate_password_hash
    import datetime

    # 1. Check if user already exists or create new
    email = data.get('email', '').lower().strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()

    # Generate a unique username based on first_name and last_name
    base_username = f"pat_{first_name.lower()}_{last_name.lower()}".replace(" ", "")[:40]
    if not base_username:
        base_username = f"pat_{email.split('@')[0]}"[:40]
    
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1

    # Check if a user with the email already exists
    user = User.query.filter_by(email=email).first()
    if not user:
        patient_role = Role.query.filter_by(name='Patient').first()
        role_id = patient_role.id if patient_role else 4
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash('patient123', method='scrypt'),
            role_id=role_id,
            is_active=True
        )
        db.session.add(user)
        db.session.flush()  # Populates user.id without committing yet

    # 2. Create the patient profile linked to the User
    patient_fields = {
        'first_name', 'last_name', 'age', 'gender', 'blood_group', 
        'phone_number', 'email', 'address', 'medical_history', 'registered_on'
    }
    patient_data = {k: v for k, v in data.items() if k in patient_fields}
    patient_data['id'] = user.id
    if 'registered_on' not in patient_data or not patient_data['registered_on']:
        patient_data['registered_on'] = datetime.date.today()

    patient = Patient(**patient_data)
    db.session.add(patient)
    db.session.commit()
    return patient


def update_patient(patient_id: int, data: dict) -> Patient:
    """Update an existing patient with ``data`` and return the refreshed model."""
    patient = Patient.query.get_or_404(patient_id)
    
    patient_fields = {
        'first_name', 'last_name', 'age', 'gender', 'blood_group', 
        'phone_number', 'email', 'address', 'medical_history', 'registered_on'
    }
    
    for attr, value in data.items():
        if attr in patient_fields:
            setattr(patient, attr, value)
            
    # Sync email with user account if modified
    if 'email' in data and patient.user:
        patient.user.email = data['email'].lower().strip()
        
    db.session.commit()
    return patient


def delete_patient(patient_id: int) -> None:
    """Soft‑delete a patient by setting ``is_active`` to ``False`` on their User account.

    A hard delete could be performed with ``db.session.delete`` but a soft delete
    preserves historical medical records while removing the patient from active
    lists.
    """
    patient = Patient.query.get_or_404(patient_id)
    if patient.user:
        patient.user.is_active = False
    db.session.commit()


def get_patient(patient_id: int) -> Patient:
    """Return a single patient (including lazy‑loaded relationships)."""
    return Patient.query.get_or_404(patient_id)


# ---------------------------------------------------------------------------
# List / Search / Pagination & Doctor Scoping
# ---------------------------------------------------------------------------

def get_doctor_associated_patient_ids(doctor_id: int) -> set:
    """Return set of patient IDs associated with a specific Doctor through appointments, consultations, or prescriptions."""
    from models.appointment import Appointment
    from models.consultation import Consultation
    from models.prescription import Prescription

    appt_pids = db.session.query(Appointment.patient_id).filter(Appointment.doctor_id == doctor_id).all()
    cons_pids = db.session.query(Consultation.patient_id).filter(Consultation.doctor_id == doctor_id).all()
    pres_pids = db.session.query(Prescription.patient_id).filter(Prescription.doctor_id == doctor_id).all()

    pids = set([p[0] for p in appt_pids if p[0]] + [p[0] for p in cons_pids if p[0]] + [p[0] for p in pres_pids if p[0]])
    return pids


def list_patients(
    page: int = 1,
    per_page: int = 10,
    sort_by: str = "last_name",
    sort_dir: str = "asc",
    search_term: Optional[str] = None,
    doctor_id: Optional[int] = None,
) -> Tuple[List[Patient], int]:
    """Return a page of patients and the total count.

    * ``sort_by`` is limited to a whitelist of safe column names.
    * ``search_term`` performs a case‑insensitive LIKE on first_name, last_name,
      email and phone_number.
    * ``doctor_id`` scopes results to patients associated with the specified Doctor.
    """
    # Whitelist allowed sort columns to prevent SQL injection via ORM
    allowed_sorts = {"first_name", "last_name", "age", "registered_on"}
    if sort_by not in allowed_sorts:
        sort_by = "last_name"
    order_clause = getattr(Patient, sort_by)
    if sort_dir.lower() == "desc":
        order_clause = order_clause.desc()
    else:
        order_clause = order_clause.asc()

    from models.user import User
    query = Patient.query.join(User).filter(User.is_active.is_(True))

    if doctor_id is not None:
        doctor_pids = get_doctor_associated_patient_ids(doctor_id)
        if doctor_pids:
            query = query.filter(Patient.id.in_(list(doctor_pids)))
        else:
            query = query.filter(Patient.id == -1)  # No patients associated

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
