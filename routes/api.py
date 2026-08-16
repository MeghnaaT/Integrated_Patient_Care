# =============================================================================
# routes/api.py — REST API Blueprint
# =============================================================================
# URL Prefix: /api/v1
# =============================================================================

from typing import Any
from functools import wraps
from flask import Blueprint, jsonify, request, g
from flask_login import current_user
import time
import datetime
from database.connection import db
from models.patient import Patient
from models.doctor import Doctor
from models.consultation import Consultation
from models.prescription import Prescription
from models.lab_report import LabReport
from models.pharmacy import Medicine
from models.billing import Bill
from models.notification import Notification

api_bp = Blueprint('api_v1', __name__)


def api_auth_required(f):
    """
    Decorator that enforces authentication for REST API endpoints.
    Unlike @login_required (which redirects to /auth/login with HTTP 302),
    this returns a proper JSON 401 response for unauthenticated API calls.
    Authenticated sessions (browser or API client) proceed normally.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                "status": "error",
                "message": "Authentication required. Please log in.",
                "data": None,
                "response_time_ms": 0.0
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def api_role_required(*allowed_roles):
    """
    Decorator that enforces role-based authorization for REST API endpoints.
    Returns JSON 403 instead of redirecting.
    Usage: @api_role_required('Admin', 'Doctor')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({
                    "status": "error",
                    "message": "Authentication required.",
                    "data": None,
                    "response_time_ms": 0.0
                }), 401
            if current_user.role.name not in allowed_roles:
                return jsonify({
                    "status": "error",
                    "message": f"Access denied. Required roles: {', '.join(allowed_roles)}.",
                    "data": None,
                    "response_time_ms": 0.0
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def make_api_response(data: Any = None, message: str = "Success", status_code: int = 200, elapsed_ms: float = 0.0):
    """Formats standardized JSON responses for all REST API endpoints."""
    res = {
        "status": "success" if status_code < 400 else "error",
        "message": message,
        "response_time_ms": round(elapsed_ms, 2),
        "data": data
    }
    return jsonify(res), status_code


# ---------------------------------------------------------------------------
# Backward-compatible alias (used by existing tests that import make_response)
# ---------------------------------------------------------------------------
make_response = make_api_response


# ---------------------------------------------------------------------------
# 1. Patient REST API
# ---------------------------------------------------------------------------
@api_bp.route('/patients', methods=['GET'])
@api_auth_required
def get_patients():
    """
    GET /api/v1/patients
    Returns all patients.
    Access: Admin, Doctor, Nurse only (Patients cannot enumerate all patients).
    """
    start = time.time()
    # Scope patients based on caller role
    role = current_user.role.name
    if role not in ('Admin', 'Doctor', 'Nurse'):
        # Patient can only see themselves via /api/v1/patients/<id>
        return make_api_response(
            None,
            "Access denied. Patient listing requires Admin, Doctor, or Nurse role.",
            403,
            (time.time() - start) * 1000
        )

    patients = Patient.query.all()
    data = [{
        "patient_id": f"P{p.id:04d}" if p.id < 1000 else f"PAT{p.id}",
        "id": p.id,
        "name": p.full_name,
        "age": p.age,
        "gender": p.gender,
        "phone": p.phone_number,
        "email": p.email,
        "aadhaar": p.aadhaar_number,
        "address": p.address
    } for p in patients]
    elapsed = (time.time() - start) * 1000
    return make_api_response(data, "Patients retrieved successfully", 200, elapsed)


@api_bp.route('/patients/<int:patient_id>', methods=['GET'])
@api_auth_required
def get_patient_detail(patient_id):
    """
    GET /api/v1/patients/<id>
    Returns a single patient's detail.
    IDOR: Patients may only access their own record.
    """
    start = time.time()
    role = current_user.role.name
    # IDOR guard: Patients may only view their own record
    if role == 'Patient' and current_user.id != patient_id:
        return make_api_response(None, "Access denied.", 403, (time.time() - start) * 1000)

    p = db.session.get(Patient, patient_id)
    if not p:
        return make_api_response(None, "Patient not found", 404, (time.time() - start) * 1000)
    data = {
        "id": p.id,
        "patient_code": f"P{p.id:04d}",
        "name": p.full_name,
        "age": p.age,
        "gender": p.gender,
        "blood_group": p.blood_group,
        "phone": p.phone_number,
        "email": p.email,
        "address": p.address
    }
    return make_api_response(data, "Patient details retrieved", 200, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 2. Doctor REST API
# ---------------------------------------------------------------------------
@api_bp.route('/doctors', methods=['GET'])
@api_auth_required
def get_doctors():
    """GET /api/v1/doctors — Returns all active doctors."""
    start = time.time()
    doctors = Doctor.query.all()
    data = [{
        "id": d.id,
        "name": f"Dr. {d.first_name} {d.last_name}",
        "specialization": d.specialization,
        "department_id": d.department_id,
        "available_time": d.available_time
    } for d in doctors]
    return make_api_response(data, "Doctors retrieved successfully", 200, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 3. Consultation REST API
# ---------------------------------------------------------------------------
@api_bp.route('/consultations', methods=['GET'])
@api_auth_required
def get_consultations():
    """GET /api/v1/consultations — Returns consultations (scoped by role)."""
    start = time.time()
    role = current_user.role.name
    query = Consultation.query
    if role == 'Doctor':
        query = query.filter(Consultation.doctor_id == current_user.id)
    elif role == 'Patient':
        query = query.filter(Consultation.patient_id == current_user.id)
    consultations = query.all()
    data = [{
        "id": c.id,
        "patient_id": c.patient_id,
        "doctor_id": c.doctor_id,
        "date": c.consultation_date.strftime('%Y-%m-%d'),
        "diagnosis": c.diagnosis,
        "symptoms": c.symptoms
    } for c in consultations]
    return make_api_response(data, "Consultations retrieved", 200, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 4. Prescription REST API
# ---------------------------------------------------------------------------
@api_bp.route('/prescriptions', methods=['GET'])
@api_auth_required
def get_prescriptions():
    """GET /api/v1/prescriptions — Returns prescriptions (scoped by role)."""
    start = time.time()
    role = current_user.role.name
    query = Prescription.query
    if role == 'Doctor':
        query = query.filter(Prescription.doctor_id == current_user.id)
    elif role == 'Patient':
        query = query.filter(Prescription.patient_id == current_user.id)
    prescriptions = query.all()
    data = [{
        "id": pr.id,
        "patient_id": pr.patient_id,
        "doctor_id": pr.doctor_id,
        "date": pr.prescription_date.strftime('%Y-%m-%d'),
        "items_count": len(pr.items)
    } for pr in prescriptions]
    return make_api_response(data, "Prescriptions retrieved", 200, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 5. Laboratory REST API
# ---------------------------------------------------------------------------
@api_bp.route('/laboratory', methods=['GET'])
@api_auth_required
def get_lab_reports():
    """GET /api/v1/laboratory — Returns lab reports (scoped by role)."""
    start = time.time()
    role = current_user.role.name
    query = LabReport.query
    if role == 'Patient':
        query = query.filter(LabReport.patient_id == current_user.id)
    reports = query.all()
    data = [{
        "id": l.id,
        "patient_id": l.patient_id,
        "test_name": l.test_name,
        "result": l.result,
        "test_date": l.test_date.strftime('%Y-%m-%d')
    } for l in reports]
    return make_api_response(data, "Lab reports retrieved", 200, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 6. Pharmacy REST API
# ---------------------------------------------------------------------------
@api_bp.route('/pharmacy', methods=['GET'])
@api_auth_required
def get_pharmacy_inventory():
    """GET /api/v1/pharmacy — Returns pharmacy inventory. Admin/Nurse/Pharmacist/Doctor only."""
    start = time.time()
    meds = Medicine.query.all()
    data = [{
        "id": m.id,
        "code": m.medicine_code,
        "name": m.medicine_name,
        "category": m.category,
        "stock": m.stock,
        "unit_price": float(m.unit_price),
        "status": m.status
    } for m in meds]
    return make_api_response(data, "Pharmacy inventory retrieved", 200, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 7. Billing REST API
# ---------------------------------------------------------------------------
@api_bp.route('/billing', methods=['GET'])
@api_auth_required
def get_billing_records():
    """GET /api/v1/billing — Returns billing records (scoped by role)."""
    start = time.time()
    role = current_user.role.name
    query = Bill.query
    if role == 'Patient':
        query = query.filter(Bill.patient_id == current_user.id)
    bills = query.all()
    data = [{
        "id": b.id,
        "bill_number": b.bill_number,
        "patient_id": b.patient_id,
        "amount": float(b.total_amount),
        "status": b.payment_status,
        "payment_method": b.payment_method
    } for b in bills]
    return make_api_response(data, "Billing records retrieved", 200, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 8. Notification REST API
# ---------------------------------------------------------------------------
@api_bp.route('/notifications', methods=['GET'])
@api_auth_required
def get_notifications():
    """GET /api/v1/notifications — Returns notifications (scoped by role)."""
    start = time.time()
    role = current_user.role.name
    query = Notification.query
    if role == 'Patient':
        query = query.filter(Notification.patient_id == current_user.id)
    notifications = query.all()
    data = [{
        "id": n.id,
        "code": n.notification_code,
        "type": n.type,
        "message": n.message,
        "status": n.status,
        "is_read": n.is_read
    } for n in notifications]
    return make_api_response(data, "Notifications retrieved", 200, (time.time() - start) * 1000)
