# =============================================================================
# services/nurse_service.py — Service layer for Nurse Management
# =============================================================================
# High-level service functions for nurse CRUD, searching, and pagination.
# =============================================================================

from typing import List, Optional, Tuple
from database.connection import db
from models.nurse import Nurse
from models.user import User
from models.role import Role
from models.department import Department
from werkzeug.security import generate_password_hash


def create_nurse(data: dict) -> Nurse:
    """Create and persist a new Nurse along with their User credential account.

    ``data`` should contain keys matching the Nurse form fields. The caller is
    responsible for validation (WTForms) before invoking this function.
    """
    email = data.get('email', '').lower().strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()

    # Generate a unique username based on first_name and last_name
    base_username = f"nurse_{first_name.lower()}_{last_name.lower()}".replace(" ", "")[:40]
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
        nurse_role = Role.query.filter_by(name='Nurse').first()
        role_id = nurse_role.id if nurse_role else 3
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash('nurse123', method='scrypt'),
            role_id=role_id,
            is_active=True
        )
        db.session.add(user)
        db.session.flush()  # Populates user.id without committing yet

    # 2. Create the Nurse profile linked to the User
    nurse_fields = {'first_name', 'last_name', 'department_id', 'contact_number', 'shift'}
    nurse_data = {k: v for k, v in data.items() if k in nurse_fields}
    nurse_data['id'] = user.id

    nurse = Nurse(**nurse_data)
    db.session.add(nurse)
    db.session.commit()
    return nurse


def update_nurse(nurse_id: int, data: dict) -> Nurse:
    """Update an existing nurse profile and sync their User email."""
    nurse = Nurse.query.get_or_404(nurse_id)
    
    nurse_fields = {'first_name', 'last_name', 'department_id', 'contact_number', 'shift'}
    
    for attr, value in data.items():
        if attr in nurse_fields:
            setattr(nurse, attr, value)
            
    # Sync email with user account if modified
    if 'email' in data and nurse.user:
        nurse.user.email = data['email'].lower().strip()
        
    db.session.commit()
    return nurse


def delete_nurse(nurse_id: int) -> None:
    """Soft‑delete a nurse by setting ``is_active`` to ``False`` on their User account."""
    nurse = Nurse.query.get_or_404(nurse_id)
    if nurse.user:
        nurse.user.is_active = False
    db.session.commit()


def get_nurse(nurse_id: int) -> Nurse:
    """Return a single nurse by ID."""
    return Nurse.query.get_or_404(nurse_id)


def list_nurses(
    page: int = 1,
    per_page: int = 10,
    sort_by: str = "last_name",
    sort_dir: str = "asc",
    search_term: Optional[str] = None,
) -> Tuple[List[Nurse], int]:
    """Return a page of active nurses and the total count.

    * ``sort_by`` is limited to a whitelist of safe column names.
    * ``search_term`` filters by name, shift, or department.
    """
    allowed_sorts = {"first_name", "last_name", "shift", "department_id"}
    if sort_by not in allowed_sorts:
        sort_by = "last_name"
    
    order_clause = getattr(Nurse, sort_by)
    if sort_dir.lower() == "desc":
        order_clause = order_clause.desc()
    else:
        order_clause = order_clause.asc()

    query = Nurse.query.join(User).filter(User.is_active.is_(True))
    
    if search_term:
        like = f"%{search_term}%"
        query = query.outerjoin(Department).filter(
            db.or_(
                Nurse.first_name.ilike(like),
                Nurse.last_name.ilike(like),
                Nurse.shift.ilike(like),
                Department.name.ilike(like)
            )
        )
        
    pagination = query.order_by(order_clause).paginate(page=page, per_page=per_page, error_out=False)
    return pagination.items, pagination.total
