# =============================================================================
# routes/api.py — REST API Blueprint
# =============================================================================
# URL Prefix: /api/v1
# =============================================================================

from flask import Blueprint, jsonify, request
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

def make_response(data: Any = None, message: str = "Success", status_code: int = 200, elapsed_ms: float = 0.0):
    """Formats standardized JSON responses."""
    res = {
        "status": "success" if status_code < 400 else "error",
        "message": message,
        "response_time_ms": round(elapsed_ms, 2),
        "data": data
    }
    return jsonify(res), status_code


# 1. Patient REST API
@api_bp.route('/patients', methods=['GET'])
def get_patients():
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
    return make_response(data, "Patients retrieved successfully", 200, elapsed)


@api_bp.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient_detail(patient_id):
    start = time.time()
    p = db.session.get(Patient, patient_id)
    if not p:
        return make_response(None, "Patient not found", 404, (time.time() - start) * 1000)
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
    return make_response(data, "Patient details retrieved", 200, (time.time() - start) * 1000)


# 2. Doctor REST API
@api_bp.route('/doctors', methods=['GET'])
def get_doctors():
    start = time.time()
    doctors = Doctor.query.all()
    data = [{
        "id": d.id,
        "name": f"Dr. {d.first_name} {d.last_name}",
        "specialization": d.specialization,
        "department_id": d.department_id,
        "available_time": d.available_time
    } for d in doctors]
    return make_response(data, "Doctors retrieved successfully", 200, (time.time() - start) * 1000)


# 3. Consultation REST API
@api_bp.route('/consultations', methods=['GET'])
def get_consultations():
    start = time.time()
    consultations = Consultation.query.all()
    data = [{
        "id": c.id,
        "patient_id": c.patient_id,
        "doctor_id": c.doctor_id,
        "date": c.consultation_date.strftime('%Y-%m-%d'),
        "diagnosis": c.diagnosis,
        "symptoms": c.symptoms
    } for c in consultations]
    return make_response(data, "Consultations retrieved", 200, (time.time() - start) * 1000)


# 4. Prescription REST API
@api_bp.route('/prescriptions', methods=['GET'])
def get_prescriptions():
    start = time.time()
    prescriptions = Prescription.query.all()
    data = [{
        "id": pr.id,
        "patient_id": pr.patient_id,
        "doctor_id": pr.doctor_id,
        "date": pr.prescription_date.strftime('%Y-%m-%d'),
        "items_count": len(pr.items)
    } for pr in prescriptions]
    return make_response(data, "Prescriptions retrieved", 200, (time.time() - start) * 1000)


# 5. Laboratory REST API
@api_bp.route('/laboratory', methods=['GET'])
def get_lab_reports():
    start = time.time()
    reports = LabReport.query.all()
    data = [{
        "id": l.id,
        "patient_id": l.patient_id,
        "test_name": l.test_name,
        "result": l.result,
        "test_date": l.test_date.strftime('%Y-%m-%d')
    } for l in reports]
    return make_response(data, "Lab reports retrieved", 200, (time.time() - start) * 1000)


# 6. Pharmacy REST API
@api_bp.route('/pharmacy', methods=['GET'])
def get_pharmacy_inventory():
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
    return make_response(data, "Pharmacy inventory retrieved", 200, (time.time() - start) * 1000)


# 7. Billing REST API
@api_bp.route('/billing', methods=['GET'])
def get_billing_records():
    start = time.time()
    bills = Bill.query.all()
    data = [{
        "id": b.id,
        "bill_number": b.bill_number,
        "patient_id": b.patient_id,
        "amount": float(b.total_amount),
        "status": b.payment_status,
        "payment_method": b.payment_method
    } for b in bills]
    return make_response(data, "Billing records retrieved", 200, (time.time() - start) * 1000)


# 8. Notification REST API
@api_bp.route('/notifications', methods=['GET'])
def get_notifications():
    start = time.time()
    notifications = Notification.query.all()
    data = [{
        "id": n.id,
        "code": n.notification_code,
        "type": n.type,
        "message": n.message,
        "status": n.status,
        "is_read": n.is_read
    } for n in notifications]
    return make_response(data, "Notifications retrieved", 200, (time.time() - start) * 1000)
