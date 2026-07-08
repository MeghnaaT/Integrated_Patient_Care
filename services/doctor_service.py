# =============================================================================
# services/doctor_service.py — Service layer for Doctor Management
# =============================================================================
# Provides high‑level database interface functions for CRUD operations and
# searching. Thin routes interact here to manage clean transactions.
# =============================================================================

from typing import List, Optional, Tuple
from database.connection import db
from models.doctor import Doctor
from models.user import User
from models.role import Role
from models.department import Department
from werkzeug.security import generate_password_hash


def create_doctor(data: dict) -> Doctor:
    """Create and persist a new Doctor along with their User credential account.

    ``data`` should contain keys matching the Doctor model fields. The caller is
    responsible for validation (WTForms) before invoking this function.
    """
    # 1. Check if user already exists or create new
    email = data.get('email_address', '').lower().strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()

    # Generate a unique username based on first_name and last_name
    base_username = f"doc_{first_name.lower()}_{last_name.lower()}".replace(" ", "")[:40]
    if not base_username:
        base_username = email.split('@')[0][:40]
    
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1

    # Check if a user with the email already exists
    user = User.query.filter_by(email=email).first()
    if not user:
        doctor_role = Role.query.filter_by(name='Doctor').first()
        role_id = doctor_role.id if doctor_role else 2
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash('doctor123', method='scrypt'),
            role_id=role_id,
            is_active=True
        )
        db.session.add(user)
        db.session.flush()  # Populates user.id without committing yet

    # 2. Create the Doctor profile linked to the User
    doctor_fields = {
        'first_name', 'last_name', 'specialization', 'qualification',
        'department_id', 'contact_number', 'email_address', 'available_time'
    }
    doctor_data = {k: v for k, v in data.items() if k in doctor_fields}
    doctor_data['id'] = user.id

    doctor = Doctor(**doctor_data)
    db.session.add(doctor)
    db.session.commit()
    return doctor


def update_doctor(doctor_id: int, data: dict) -> Doctor:
    """Update an existing doctor profile with ``data`` and return the refreshed model."""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    doctor_fields = {
        'first_name', 'last_name', 'specialization', 'qualification',
        'department_id', 'contact_number', 'email_address', 'available_time'
    }
    
    for attr, value in data.items():
        if attr in doctor_fields:
            setattr(doctor, attr, value)
            
    # Sync email with user account if modified
    if 'email_address' in data and doctor.user:
        doctor.user.email = data['email_address'].lower().strip()
        
    db.session.commit()
    return doctor


def delete_doctor(doctor_id: int) -> None:
    """Soft‑delete a doctor by setting ``is_active`` to ``False`` on their User account."""
    doctor = Doctor.query.get_or_404(doctor_id)
    if doctor.user:
        doctor.user.is_active = False
    db.session.commit()


def get_doctor(doctor_id: int) -> Doctor:
    """Return a single doctor (including relationships)."""
    return Doctor.query.get_or_404(doctor_id)


def list_doctors(
    page: int = 1,
    per_page: int = 10,
    sort_by: str = "last_name",
    sort_dir: str = "asc",
    search_term: Optional[str] = None,
) -> Tuple[List[Doctor], int]:
    """Return a page of active doctors and the total count.

    * ``sort_by`` is limited to a whitelist of safe column names.
    * ``search_term`` filters by first_name, last_name, specialization, or department.
    """
    # Whitelist allowed sort columns to prevent SQL injection
    allowed_sorts = {"first_name", "last_name", "specialization", "department_id"}
    if sort_by not in allowed_sorts:
        sort_by = "last_name"
    
    order_clause = getattr(Doctor, sort_by)
    if sort_dir.lower() == "desc":
        order_clause = order_clause.desc()
    else:
        order_clause = order_clause.asc()

    query = Doctor.query.join(User).filter(User.is_active.is_(True))
    
    if search_term:
        like = f"%{search_term}%"
        query = query.outerjoin(Department).filter(
            db.or_(
                Doctor.first_name.ilike(like),
                Doctor.last_name.ilike(like),
                Doctor.specialization.ilike(like),
                Department.name.ilike(like)
            )
        )
        
    pagination = query.order_by(order_clause).paginate(page=page, per_page=per_page, error_out=False)
    return pagination.items, pagination.total
