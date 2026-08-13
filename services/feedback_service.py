# =============================================================================
# services/feedback_service.py — Patient Feedback & Satisfaction Business Engine
# =============================================================================

import datetime
from typing import Dict, List, Any, Tuple, Optional
from sqlalchemy import func
from database.connection import db

from models.feedback import Feedback
from models.patient import Patient
from models.doctor import Doctor
from models.department import Department
from models.consultation import Consultation
from models.lab_report import LabReport
from models.pharmacy import MedicineDispensation

def generate_feedback_code() -> str:
    """Generates unique incremental feedback code (e.g. FBK1001)."""
    last_fbk = Feedback.query.order_by(Feedback.id.desc()).first()
    if not last_fbk:
        return 'FBK1001'
    return f"FBK{1000 + last_fbk.id + 1}"

def can_patient_submit_feedback(patient_id: int, service_type: str, consultation_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Verifies that the patient received the service before allowing feedback submission.
    Prevents duplicate submissions for the exact same consultation.
    """
    if service_type == 'Doctor Performance' or consultation_id:
        if consultation_id:
            # Check if duplicate feedback exists for this consultation
            existing = Feedback.query.filter_by(patient_id=patient_id, consultation_id=consultation_id).first()
            if existing:
                return False, "You have already submitted feedback for this consultation."
        # Verify patient has at least 1 consultation
        has_consult = Consultation.query.filter_by(patient_id=patient_id).first()
        if not has_consult:
            return False, "You can only rate Doctor Performance after receiving a consultation."
            
    elif service_type == 'Laboratory Service':
        has_lab = LabReport.query.filter_by(patient_id=patient_id).first()
        if not has_lab:
            return False, "Feedback restricted: No laboratory tests found for your account."

    elif service_type == 'Pharmacy Service':
        has_disp = MedicineDispensation.query.filter_by(patient_id=patient_id).first()
        if not has_disp:
            return False, "Feedback restricted: No pharmacy dispensations found for your account."

    return True, "Eligible"

def create_feedback(data: Dict[str, Any]) -> Feedback:
    """Creates and persists a new Feedback record."""
    patient_id = data.get('patient_id')
    service_type = data.get('service_type', 'Doctor Performance')
    consultation_id = data.get('consultation_id')
    rating = int(data.get('rating', 5))

    if rating < 1 or rating > 5:
        raise ValueError("Rating must be an integer between 1 and 5 stars.")

    can_submit, msg = can_patient_submit_feedback(patient_id, service_type, consultation_id)
    if not can_submit:
        raise ValueError(msg)

    fbk = Feedback(
        feedback_code=generate_feedback_code(),
        patient_id=patient_id,
        doctor_id=data.get('doctor_id'),
        department_id=data.get('department_id'),
        consultation_id=consultation_id,
        service_type=service_type,
        rating=rating,
        comment=data.get('comment', '').strip(),
        status='Published',
        created_date=datetime.date.today()
    )
    db.session.add(fbk)
    db.session.commit()
    return fbk

def get_patient_feedback_history(patient_id: int) -> List[Feedback]:
    """Retrieves all feedback records submitted by a patient."""
    return Feedback.query.filter_by(patient_id=patient_id).order_by(Feedback.created_at.desc()).all()

def get_all_feedback(filters: Optional[Dict[str, Any]] = None, page: int = 1, per_page: int = 10) -> Tuple[List[Feedback], int]:
    """Returns paginated feedback records for Administrative review."""
    query = Feedback.query

    if filters:
        if filters.get('service_type'):
            query = query.filter_by(service_type=filters['service_type'])
        if filters.get('rating'):
            query = query.filter_by(rating=int(filters['rating']))
        if filters.get('doctor_id'):
            query = query.filter_by(doctor_id=int(filters['doctor_id']))
        if filters.get('department_id'):
            query = query.filter_by(department_id=int(filters['department_id']))
        if filters.get('date_from'):
            query = query.filter(Feedback.created_date >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(Feedback.created_date <= filters['date_to'])

    pagination = query.order_by(Feedback.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return pagination.items, pagination.total

def get_feedback_satisfaction_statistics() -> Dict[str, Any]:
    """Computes comprehensive patient satisfaction statistics and ratings breakdowns."""
    total_reviews = Feedback.query.count()
    if total_reviews == 0:
        return {
            'overall_avg_rating': 4.8,
            'satisfaction_score_pct': 96.0,
            'total_reviews': 0,
            'rating_breakdown': {5: 0, 4: 0, 3: 0, 2: 0, 1: 0},
            'service_wise_ratings': {},
            'doctor_wise_ratings': [],
            'department_wise_ratings': []
        }

    avg_rating_res = db.session.query(func.avg(Feedback.rating)).scalar() or 4.8
    overall_avg_rating = round(float(avg_rating_res), 2)
    satisfaction_score_pct = round((overall_avg_rating / 5.0) * 100.0, 1)

    # Breakdown by star rating
    star_counts = db.session.query(Feedback.rating, func.count(Feedback.id)).group_by(Feedback.rating).all()
    rating_breakdown = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r, c in star_counts:
        rating_breakdown[r] = c

    # Service-wise ratings
    svc_counts = db.session.query(Feedback.service_type, func.avg(Feedback.rating)).group_by(Feedback.service_type).all()
    service_wise_ratings = {st: round(float(avg_r), 2) for st, avg_r in svc_counts}

    # Doctor-wise ratings
    doc_ratings_q = db.session.query(Doctor, func.avg(Feedback.rating), func.count(Feedback.id))\
        .join(Feedback, Doctor.id == Feedback.doctor_id)\
        .group_by(Doctor.id).all()
    doctor_wise_ratings = [
        {
            'doctor_id': d.id,
            'doctor_name': f"Dr. {d.first_name} {d.last_name}",
            'department': d.department.name if d.department else 'General',
            'avg_rating': round(float(avg_r), 2),
            'review_count': cnt
        } for d, avg_r, cnt in doc_ratings_q
    ]

    # Department-wise ratings
    dept_ratings_q = db.session.query(Department, func.avg(Feedback.rating), func.count(Feedback.id))\
        .join(Feedback, Department.id == Feedback.department_id)\
        .group_by(Department.id).all()
    department_wise_ratings = [
        {
            'department_id': dept.id,
            'department_name': dept.name,
            'avg_rating': round(float(avg_r), 2),
            'review_count': cnt
        } for dept, avg_r, cnt in dept_ratings_q
    ]

    return {
        'overall_avg_rating': overall_avg_rating,
        'satisfaction_score_pct': satisfaction_score_pct,
        'total_reviews': total_reviews,
        'rating_breakdown': rating_breakdown,
        'service_wise_ratings': service_wise_ratings,
        'doctor_wise_ratings': doctor_wise_ratings,
        'department_wise_ratings': department_wise_ratings
    }
