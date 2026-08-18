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
                "success": False,
                "error": "Authentication required"
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
                    "success": False,
                    "error": "Authentication required"
                }), 401
            if current_user.role.name not in allowed_roles:
                return jsonify({
                    "success": False,
                    "error": "Insufficient permissions"
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
@api_role_required('Admin', 'Doctor', 'Nurse', 'Receptionist')
def get_patients():
    """
    GET /api/v1/patients
    Returns all patients.
    Access: Admin, Doctor, Nurse, Receptionist.
    """
    start = time.time()
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
@api_role_required('Admin', 'Doctor', 'Nurse', 'Receptionist', 'Patient')
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
        return jsonify({
            "success": False,
            "error": "Insufficient permissions"
        }), 403

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
@api_role_required('Admin', 'Doctor', 'Nurse', 'Patient', 'Receptionist')
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
@api_role_required('Admin', 'Doctor', 'Nurse', 'Patient')
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
@api_role_required('Admin', 'Doctor', 'Nurse', 'Patient')
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
@api_role_required('Admin', 'Doctor', 'Nurse', 'Patient', 'Laboratory Staff')
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
@api_role_required('Admin', 'Doctor', 'Nurse', 'Pharmacist')
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
@api_role_required('Admin', 'Nurse', 'Patient')
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
@api_role_required('Admin', 'Nurse', 'Patient')
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


# =============================================================================
# REST API WRITE/CRUD ENDPOINTS (Milestone 3 Compliance Phase)
# =============================================================================

# ---------------------------------------------------------------------------
# 1. Patient Write REST API
# ---------------------------------------------------------------------------
@api_bp.route('/patients', methods=['POST'])
@api_role_required('Admin', 'Nurse', 'Receptionist')
def api_create_patient():
    """POST /api/v1/patients — Creates a new patient."""
    start = time.time()
    try:
        data = request.get_json() or {}
        
        # Required fields check
        required = ['first_name', 'last_name', 'email', 'phone_number', 'gender', 'age', 'address']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return make_api_response(None, f"Missing required fields: {', '.join(missing)}", 400, (time.time() - start) * 1000)

        # Email format & uniqueness
        email = data.get('email', '').lower().strip()
        if '@' not in email or email.count('@') != 1:
            return make_api_response(None, "Invalid email format.", 400, (time.time() - start) * 1000)
        
        from models.user import User
        if User.query.filter_by(email=email).first():
            return make_api_response(None, "An account with that email already exists.", 409, (time.time() - start) * 1000)

        # Age validation
        try:
            age = int(data.get('age'))
            if not (0 <= age <= 150):
                raise ValueError
        except (TypeError, ValueError):
            return make_api_response(None, "Age must be an integer between 0 and 150.", 400, (time.time() - start) * 1000)

        # Gender validation
        gender = data.get('gender')
        if gender not in ['Male', 'Female', 'Other']:
            return make_api_response(None, "Gender must be 'Male', 'Female', or 'Other'.", 400, (time.time() - start) * 1000)

        # Phone validation
        import re
        phone = data.get('phone_number')
        if not re.match(r"^\+?[0-9]{7,15}$", phone):
            return make_api_response(None, "Enter a valid phone number.", 400, (time.time() - start) * 1000)

        # Call service
        from services.patient_service import create_patient
        patient = create_patient(data)
        
        res_data = {
            "id": patient.id,
            "patient_code": f"P{patient.id:04d}",
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "email": patient.email,
            "phone_number": patient.phone_number
        }
        return make_api_response(res_data, "Patient created successfully", 201, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)


@api_bp.route('/patients/<int:patient_id>', methods=['PUT'])
@api_role_required('Admin', 'Nurse', 'Receptionist', 'Patient')
def api_update_patient(patient_id):
    """PUT /api/v1/patients/<id> — Updates an existing patient."""
    start = time.time()
    try:
        # IDOR Guard
        if current_user.role.name == 'Patient' and current_user.id != patient_id:
            return jsonify({"success": False, "error": "Insufficient permissions"}), 403

        patient = db.session.get(Patient, patient_id)
        if not patient:
            return make_api_response(None, "Patient not found", 404, (time.time() - start) * 1000)

        data = request.get_json() or {}

        # Email format & uniqueness if updated
        if 'email' in data:
            email = data.get('email', '').lower().strip()
            if '@' not in email or email.count('@') != 1:
                return make_api_response(None, "Invalid email format.", 400, (time.time() - start) * 1000)
            from models.user import User
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != patient_id:
                return make_api_response(None, "An account with that email already exists.", 409, (time.time() - start) * 1000)

        # Age validation if updated
        if 'age' in data:
            try:
                age = int(data.get('age'))
                if not (0 <= age <= 150):
                    raise ValueError
            except (TypeError, ValueError):
                return make_api_response(None, "Age must be an integer between 0 and 150.", 400, (time.time() - start) * 1000)

        # Gender validation if updated
        if 'gender' in data:
            gender = data.get('gender')
            if gender not in ['Male', 'Female', 'Other']:
                return make_api_response(None, "Gender must be 'Male', 'Female', or 'Other'.", 400, (time.time() - start) * 1000)

        # Phone validation if updated
        if 'phone_number' in data:
            import re
            phone = data.get('phone_number')
            if not re.match(r"^\+?[0-9]{7,15}$", phone):
                return make_api_response(None, "Enter a valid phone number.", 400, (time.time() - start) * 1000)

        # Call service
        from services.patient_service import update_patient
        updated = update_patient(patient_id, data)
        res_data = {
            "id": updated.id,
            "patient_code": f"P{updated.id:04d}",
            "first_name": updated.first_name,
            "last_name": updated.last_name,
            "email": updated.email,
            "phone_number": updated.phone_number
        }
        return make_api_response(res_data, "Patient updated successfully", 200, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)


@api_bp.route('/patients/<int:patient_id>', methods=['DELETE'])
@api_role_required('Admin')
def api_delete_patient(patient_id):
    """DELETE /api/v1/patients/<id> — Soft-deletes a patient user."""
    start = time.time()
    try:
        patient = db.session.get(Patient, patient_id)
        if not patient:
            return make_api_response(None, "Patient not found", 404, (time.time() - start) * 1000)

        from services.patient_service import delete_patient
        delete_patient(patient_id)
        return make_api_response(None, "Patient deleted successfully", 200, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 2. Appointment Write REST API
# ---------------------------------------------------------------------------
@api_bp.route('/appointments', methods=['POST'])
@api_role_required('Admin', 'Nurse', 'Receptionist', 'Patient')
def api_create_appointment():
    """POST /api/v1/appointments — Books a new appointment."""
    start = time.time()
    try:
        data = request.get_json() or {}
        role = current_user.role.name

        # Force patient ID and status if role is Patient
        if role == 'Patient':
            patient_id = current_user.id
            status = 'Pending'
        else:
            patient_id = data.get('patient_id')
            status = data.get('status', 'Confirmed')

        doctor_id = data.get('doctor_id')
        date_str = data.get('appointment_date')
        time_str = data.get('appointment_time')

        if not patient_id or not doctor_id or not date_str or not time_str:
            return make_api_response(None, "Missing required scheduling fields.", 400, (time.time() - start) * 1000)

        # Verify patient & doctor existence
        patient = db.session.get(Patient, patient_id)
        if not patient:
            return make_api_response(None, "Patient not found.", 400, (time.time() - start) * 1000)

        doctor = db.session.get(Doctor, doctor_id)
        if not doctor:
            return make_api_response(None, "Doctor not found.", 400, (time.time() - start) * 1000)

        # Parse date & time
        try:
            appt_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return make_api_response(None, "Invalid date format. Use YYYY-MM-DD.", 400, (time.time() - start) * 1000)

        appt_time = None
        for fmt in ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"]:
            try:
                appt_time = datetime.datetime.strptime(time_str, fmt).time()
                break
            except ValueError:
                pass
        if not appt_time:
            return make_api_response(None, "Invalid time format. Use HH:MM, HH:MM:SS, or HH:MM AM/PM.", 400, (time.time() - start) * 1000)

        # Check past date
        if appt_date < datetime.date.today():
            return make_api_response(None, "Appointment date cannot be in the past.", 400, (time.time() - start) * 1000)

        # Check availability & conflicts
        from services.appointment_service import check_doctor_availability, check_patient_conflict, book_appointment
        ok, err = check_doctor_availability(doctor_id, appt_date, appt_time)
        if not ok:
            return make_api_response(None, err, 409, (time.time() - start) * 1000)

        ok, err = check_patient_conflict(patient_id, appt_date, appt_time)
        if not ok:
            return make_api_response(None, err, 409, (time.time() - start) * 1000)

        # Book appointment
        appt_data = {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'appointment_date': appt_date,
            'appointment_time': appt_time,
            'status': status
        }
        appt, err = book_appointment(appt_data)
        if not appt:
            return make_api_response(None, err, 400, (time.time() - start) * 1000)

        res_data = {
            "id": appt.id,
            "patient_id": appt.patient_id,
            "doctor_id": appt.doctor_id,
            "appointment_date": appt.appointment_date.strftime('%Y-%m-%d'),
            "appointment_time": appt.appointment_time.strftime('%H:%M:%S'),
            "status": appt.status
        }
        return make_api_response(res_data, "Appointment booked successfully", 201, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)


@api_bp.route('/appointments/<int:appt_id>', methods=['PUT'])
@api_role_required('Admin', 'Nurse', 'Receptionist', 'Patient')
def api_update_appointment(appt_id):
    """PUT /api/v1/appointments/<id> — Updates an existing appointment."""
    start = time.time()
    try:
        from models.appointment import Appointment
        appt = db.session.get(Appointment, appt_id)
        if not appt:
            return make_api_response(None, "Appointment not found.", 404, (time.time() - start) * 1000)

        role = current_user.role.name
        # IDOR Guard
        if role == 'Patient' and appt.patient_id != current_user.id:
            return jsonify({"success": False, "error": "Insufficient permissions"}), 403

        data = request.get_json() or {}

        # Override status / patient if Patient role
        if role == 'Patient':
            if 'patient_id' in data and data['patient_id'] != current_user.id:
                return make_api_response(None, "Cannot reschedule appointment for another patient.", 400, (time.time() - start) * 1000)
            patient_id = current_user.id
            status = 'Pending'
        else:
            patient_id = data.get('patient_id', appt.patient_id)
            status = data.get('status', appt.status)

        doctor_id = data.get('doctor_id', appt.doctor_id)
        date_str = data.get('appointment_date')
        time_str = data.get('appointment_time')

        # Parse date & time
        if date_str:
            try:
                appt_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return make_api_response(None, "Invalid date format. Use YYYY-MM-DD.", 400, (time.time() - start) * 1000)
        else:
            appt_date = appt.appointment_date

        if time_str:
            appt_time = None
            for fmt in ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"]:
                try:
                    appt_time = datetime.datetime.strptime(time_str, fmt).time()
                    break
                except ValueError:
                    pass
            if not appt_time:
                return make_api_response(None, "Invalid time format. Use HH:MM, HH:MM:SS, or HH:MM AM/PM.", 400, (time.time() - start) * 1000)
        else:
            appt_time = appt.appointment_time

        # Check past date
        if appt_date != appt.appointment_date and appt_date < datetime.date.today():
            return make_api_response(None, "Appointment date cannot be in the past.", 400, (time.time() - start) * 1000)

        # Check doctor/patient exist
        if not db.session.get(Patient, patient_id):
            return make_api_response(None, "Patient not found.", 400, (time.time() - start) * 1000)
        if not db.session.get(Doctor, doctor_id):
            return make_api_response(None, "Doctor not found.", 400, (time.time() - start) * 1000)

        # Check availability & conflicts
        from services.appointment_service import check_doctor_availability, check_patient_conflict, update_appointment
        ok, err = check_doctor_availability(doctor_id, appt_date, appt_time, exclude_appt_id=appt_id)
        if not ok:
            return make_api_response(None, err, 409, (time.time() - start) * 1000)

        ok, err = check_patient_conflict(patient_id, appt_date, appt_time, exclude_appt_id=appt_id)
        if not ok:
            return make_api_response(None, err, 409, (time.time() - start) * 1000)

        # Update appointment
        appt_data = {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'appointment_date': appt_date,
            'appointment_time': appt_time,
            'status': status
        }
        updated, err = update_appointment(appt_id, appt_data)
        if not updated:
            return make_api_response(None, err, 400, (time.time() - start) * 1000)

        res_data = {
            "id": updated.id,
            "patient_id": updated.patient_id,
            "doctor_id": updated.doctor_id,
            "appointment_date": updated.appointment_date.strftime('%Y-%m-%d'),
            "appointment_time": updated.appointment_time.strftime('%H:%M:%S'),
            "status": updated.status
        }
        return make_api_response(res_data, "Appointment updated successfully", 200, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)


@api_bp.route('/appointments/<int:appt_id>', methods=['DELETE'])
@api_role_required('Admin', 'Nurse', 'Receptionist', 'Patient')
def api_delete_appointment(appt_id):
    """DELETE /api/v1/appointments/<id> — Cancels (soft-deletes) an appointment."""
    start = time.time()
    try:
        from models.appointment import Appointment
        appt = db.session.get(Appointment, appt_id)
        if not appt:
            return make_api_response(None, "Appointment not found.", 404, (time.time() - start) * 1000)

        role = current_user.role.name
        # IDOR Guard
        if role == 'Patient' and appt.patient_id != current_user.id:
            return jsonify({"success": False, "error": "Insufficient permissions"}), 403

        from services.appointment_service import cancel_appointment
        cancelled = cancel_appointment(appt_id)
        res_data = {
            "id": cancelled.id,
            "status": cancelled.status
        }
        return make_api_response(res_data, "Appointment cancelled successfully", 200, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 3. Consultation Write REST API
# ---------------------------------------------------------------------------
@api_bp.route('/consultations', methods=['POST'])
@api_role_required('Admin', 'Doctor')
def api_create_consultation():
    """POST /api/v1/consultations — Creates a consultation report."""
    start = time.time()
    try:
        data = request.get_json() or {}
        role = current_user.role.name

        if role == 'Doctor':
            doctor_id = current_user.id
        else:
            doctor_id = data.get('doctor_id')

        patient_id = data.get('patient_id')
        date_str = data.get('consultation_date')
        symptoms = data.get('symptoms')
        diagnosis = data.get('diagnosis')
        treatment_notes = data.get('treatment_notes')

        if not patient_id or not doctor_id or not date_str or not symptoms or not diagnosis or not treatment_notes:
            return make_api_response(None, "Missing required consultation fields.", 400, (time.time() - start) * 1000)

        patient = db.session.get(Patient, patient_id)
        if not patient:
            return make_api_response(None, "Patient not found.", 400, (time.time() - start) * 1000)

        doctor = db.session.get(Doctor, doctor_id)
        if not doctor:
            return make_api_response(None, "Doctor not found.", 400, (time.time() - start) * 1000)

        try:
            cons_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return make_api_response(None, "Invalid date format. Use YYYY-MM-DD.", 400, (time.time() - start) * 1000)

        from services.consultation_service import create_consultation
        cons = create_consultation(patient_id, doctor_id, cons_date, symptoms, diagnosis, treatment_notes)
        res_data = {
            "id": cons.id,
            "patient_id": cons.patient_id,
            "doctor_id": cons.doctor_id,
            "consultation_date": cons.consultation_date.strftime('%Y-%m-%d'),
            "diagnosis": cons.diagnosis
        }
        return make_api_response(res_data, "Consultation created successfully", 201, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 4. Prescription Write REST API
# ---------------------------------------------------------------------------
@api_bp.route('/prescriptions', methods=['POST'])
@api_role_required('Admin', 'Doctor')
def api_create_prescription():
    """POST /api/v1/prescriptions — Creates a prescription."""
    start = time.time()
    try:
        data = request.get_json() or {}
        role = current_user.role.name

        if role == 'Doctor':
            doctor_id = current_user.id
        else:
            doctor_id = data.get('doctor_id')

        patient_id = data.get('patient_id')
        date_str = data.get('prescription_date')
        special_instructions = data.get('special_instructions', '')
        items = data.get('items', [])
        consultation_id = data.get('consultation_id')

        if not patient_id or not doctor_id or not date_str or not items:
            return make_api_response(None, "Missing required prescription fields.", 400, (time.time() - start) * 1000)

        if not isinstance(items, list) or len(items) == 0:
            return make_api_response(None, "Prescription must contain at least one item.", 400, (time.time() - start) * 1000)

        for it in items:
            if not it.get('medicine_name'):
                return make_api_response(None, "Each item must have a medicine_name.", 400, (time.time() - start) * 1000)

        patient = db.session.get(Patient, patient_id)
        if not patient:
            return make_api_response(None, "Patient not found.", 400, (time.time() - start) * 1000)

        doctor = db.session.get(Doctor, doctor_id)
        if not doctor:
            return make_api_response(None, "Doctor not found.", 400, (time.time() - start) * 1000)

        if consultation_id:
            from models.consultation import Consultation
            if not db.session.get(Consultation, consultation_id):
                return make_api_response(None, "Consultation not found.", 400, (time.time() - start) * 1000)

        try:
            pres_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return make_api_response(None, "Invalid date format. Use YYYY-MM-DD.", 400, (time.time() - start) * 1000)

        from services.prescription_service import create_prescription
        pres = create_prescription(patient_id, doctor_id, pres_date, special_instructions, items, consultation_id)
        res_data = {
            "id": pres.id,
            "patient_id": pres.patient_id,
            "doctor_id": pres.doctor_id,
            "prescription_date": pres.prescription_date.strftime('%Y-%m-%d'),
            "items_count": len(pres.items)
        }
        return make_api_response(res_data, "Prescription created successfully", 201, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 5. Laboratory Write REST API
# ---------------------------------------------------------------------------
@api_bp.route('/laboratory', methods=['POST'])
@api_role_required('Admin', 'Doctor', 'Laboratory Staff')
def api_create_lab_report():
    """POST /api/v1/laboratory — Creates a lab test report."""
    start = time.time()
    try:
        data = request.get_json() or {}

        patient_id = data.get('patient_id')
        doctor_id = data.get('doctor_id')
        test_name = data.get('test_name')
        date_str = data.get('test_date')
        result = data.get('result')
        remarks = data.get('remarks')

        if not patient_id or not doctor_id or not test_name or not date_str or not result:
            return make_api_response(None, "Missing required laboratory report fields.", 400, (time.time() - start) * 1000)

        patient = db.session.get(Patient, patient_id)
        if not patient:
            return make_api_response(None, "Patient not found.", 400, (time.time() - start) * 1000)

        doctor = db.session.get(Doctor, doctor_id)
        if not doctor:
            return make_api_response(None, "Doctor not found.", 400, (time.time() - start) * 1000)

        try:
            test_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return make_api_response(None, "Invalid date format. Use YYYY-MM-DD.", 400, (time.time() - start) * 1000)

        from services.lab_service import create_lab_report
        report = create_lab_report(patient_id, doctor_id, test_name, test_date, result, remarks)
        res_data = {
            "id": report.id,
            "patient_id": report.patient_id,
            "test_name": report.test_name,
            "result": report.result,
            "test_date": report.test_date.strftime('%Y-%m-%d')
        }
        return make_api_response(res_data, "Laboratory report created successfully", 201, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 6. Pharmacy Write REST API
# ---------------------------------------------------------------------------
@api_bp.route('/pharmacy', methods=['POST'])
@api_role_required('Admin', 'Pharmacist')
def api_create_medicine():
    """POST /api/v1/pharmacy — Adds a medicine to inventory."""
    start = time.time()
    try:
        data = request.get_json() or {}

        code = data.get('medicine_code')
        name = data.get('medicine_name') or data.get('name')
        category = data.get('category')
        manufacturer = data.get('manufacturer')
        stock = data.get('stock')
        price = data.get('unit_price')
        date_str = data.get('expiry_date')

        if not code or not name or not category or not manufacturer or stock is None or price is None or not date_str:
            return make_api_response(None, "Missing required medicine fields.", 400, (time.time() - start) * 1000)

        # Uniqueness check for code
        from models.pharmacy import Medicine
        if Medicine.query.filter_by(medicine_code=code).first():
            return make_api_response(None, "A medicine with that code already exists.", 409, (time.time() - start) * 1000)

        # Number validation
        try:
            stock = int(stock)
            if stock < 0:
                raise ValueError
        except (TypeError, ValueError):
            return make_api_response(None, "Stock must be a non-negative integer.", 400, (time.time() - start) * 1000)

        try:
            price = float(price)
            if price < 0.0:
                raise ValueError
        except (TypeError, ValueError):
            return make_api_response(None, "Unit price must be a non-negative float.", 400, (time.time() - start) * 1000)

        # Parse date
        try:
            expiry_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return make_api_response(None, "Invalid date format. Use YYYY-MM-DD.", 400, (time.time() - start) * 1000)

        from services.pharmacy_service import add_medicine
        med = add_medicine(code, name, category, manufacturer, stock, price, expiry_date)
        res_data = {
            "id": med.id,
            "medicine_code": med.medicine_code,
            "medicine_name": med.medicine_name,
            "category": med.category,
            "stock": med.stock,
            "unit_price": float(med.unit_price)
        }
        return make_api_response(res_data, "Medicine added successfully", 201, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)


# ---------------------------------------------------------------------------
# 7. Billing Write REST API
# ---------------------------------------------------------------------------
@api_bp.route('/billing', methods=['POST'])
@api_role_required('Admin', 'Nurse')
def api_create_bill():
    """POST /api/v1/billing — Generates an itemized bill for a patient."""
    start = time.time()
    try:
        data = request.get_json() or {}

        patient_id = data.get('patient_id')
        payment_method = data.get('payment_method', 'UPI')
        transaction_id = data.get('transaction_id')
        discount = data.get('discount', 0.0)
        tax = data.get('tax_amount', 0.0)

        if not patient_id:
            return make_api_response(None, "Missing patient_id.", 400, (time.time() - start) * 1000)

        patient = db.session.get(Patient, patient_id)
        if not patient:
            return make_api_response(None, "Patient not found.", 400, (time.time() - start) * 1000)

        try:
            discount = float(discount)
            if discount < 0.0:
                raise ValueError
        except (TypeError, ValueError):
            return make_api_response(None, "Discount must be a non-negative float.", 400, (time.time() - start) * 1000)

        try:
            tax = float(tax)
            if tax < 0.0:
                raise ValueError
        except (TypeError, ValueError):
            return make_api_response(None, "Tax must be a non-negative float.", 400, (time.time() - start) * 1000)

        from services.billing_service import generate_bill_for_patient
        bill = generate_bill_for_patient(patient_id, payment_method, transaction_id, discount, tax)
        res_data = {
            "id": bill.id,
            "bill_number": bill.bill_number,
            "patient_id": bill.patient_id,
            "total_amount": float(bill.total_amount),
            "payment_status": bill.payment_status
        }
        return make_api_response(res_data, "Invoice generated successfully", 201, (time.time() - start) * 1000)
    except Exception as e:
        return make_api_response(None, f"Unexpected error: {str(e)}", 500, (time.time() - start) * 1000)
