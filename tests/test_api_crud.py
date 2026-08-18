# =============================================================================
# tests/test_api_crud.py — API CRUD & Validations Hardening Test Suite
# =============================================================================

import unittest
import os
import sys
import json
import datetime
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.user import User
from models.role import Role
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.consultation import Consultation
from models.prescription import Prescription
from models.lab_report import LabReport
from models.pharmacy import Medicine
from models.billing import Bill

class APICrudTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('default')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self._ensure_test_roles_and_users()

    def _ensure_test_roles_and_users(self):
        # Ensure roles exist
        roles = ['Admin', 'Doctor', 'Nurse', 'Patient', 'Pharmacist', 'Laboratory Staff', 'Receptionist']
        for r_name in roles:
            r = Role.query.filter_by(name=r_name).first()
            if not r:
                r = Role(name=r_name, description=f"{r_name} role")
                db.session.add(r)
        db.session.commit()

        # Create Pharmacist test user if not exists
        pharmacist_role = Role.query.filter_by(name='Pharmacist').first()
        ph = User.query.filter_by(email='pharmacist_test@ipcms.com').first()
        if not ph:
            ph = User(
                username='pharmacist_test_user',
                email='pharmacist_test@ipcms.com',
                password_hash=generate_password_hash('password123', method='scrypt'),
                role_id=pharmacist_role.id,
                is_active=True
            )
            db.session.add(ph)

        # Create Laboratory Staff test user if not exists
        lab_role = Role.query.filter_by(name='Laboratory Staff').first()
        lb = User.query.filter_by(email='labstaff_test@ipcms.com').first()
        if not lb:
            lb = User(
                username='labstaff_test_user',
                email='labstaff_test@ipcms.com',
                password_hash=generate_password_hash('password123', method='scrypt'),
                role_id=lab_role.id,
                is_active=True
            )
            db.session.add(lb)

        # Create Receptionist test user if not exists
        receptionist_role = Role.query.filter_by(name='Receptionist').first()
        rc = User.query.filter_by(email='receptionist_test@ipcms.com').first()
        if not rc:
            rc = User(
                username='receptionist_test_user',
                email='receptionist_test@ipcms.com',
                password_hash=generate_password_hash('password123', method='scrypt'),
                role_id=receptionist_role.id,
                is_active=True
            )
            db.session.add(rc)

        # Create Patient B for IDOR testing
        patient_role = Role.query.filter_by(name='Patient').first()
        p_b_user = User.query.filter_by(email='patient_b@ipcms.com').first()
        if not p_b_user:
            p_b_user = User(
                username='patient_b_user',
                email='patient_b@ipcms.com',
                password_hash=generate_password_hash('password123', method='scrypt'),
                role_id=patient_role.id,
                is_active=True
            )
            db.session.add(p_b_user)
            db.session.flush()

            p_b = Patient(
                id=p_b_user.id,
                first_name='Patient',
                last_name='B',
                age=30,
                gender='Female',
                blood_group='O-',
                phone_number='1234567899',
                email='patient_b@ipcms.com',
                address='456 Street, Chennai',
                registered_on=db.func.current_date()
            )
            db.session.add(p_b)

        db.session.commit()

    def tearDown(self):
        # Clean up any created test patients or users
        User.query.filter(User.email.in_([
            'pharmacist_test@ipcms.com',
            'labstaff_test@ipcms.com',
            'receptionist_test@ipcms.com',
            'patient_b@ipcms.com',
            'jane.doe@ipcms.com'
        ])).delete(synchronize_session=False)

        Patient.query.filter(Patient.email.in_([
            'patient_b@ipcms.com',
            'jane.doe@ipcms.com'
        ])).delete(synchronize_session=False)

        Medicine.query.filter(Medicine.medicine_code == 'TESTMED999').delete(synchronize_session=False)

        # Restore Patient 4 original data
        p4 = db.session.get(Patient, 4)
        if p4:
            p4.phone_number = "9876543210"
            p4.address = "123, Green Street, Chennai - 600001"
            if p4.user:
                p4.user.is_active = True

        db.session.commit()
        db.session.rollback()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password,
            'remember_me': False
        })

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    # -------------------------------------------------------------------------
    # 1. Patient CRUD Tests
    # -------------------------------------------------------------------------
    def test_01_patient_create_success(self):
        """1. Nurse can create a patient with valid details."""
        self.login('nurse@ipcms.com', 'nurse123')
        payload = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@ipcms.com",
            "phone_number": "9876543219",
            "gender": "Female",
            "age": 25,
            "address": "123 Green Avenue, Chennai",
            "blood_group": "B+"
        }
        res = self.client.post('/api/v1/patients', json=payload)
        self.assertEqual(res.status_code, 201)
        json_data = res.get_json()
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['data']['email'], 'jane.doe@ipcms.com')

        # Check database
        p = Patient.query.filter_by(email='jane.doe@ipcms.com').first()
        self.assertIsNotNone(p)
        self.assertEqual(p.first_name, 'Jane')

    def test_02_patient_create_validation_failures(self):
        """2. Patient creation fails on invalid fields or duplicate email."""
        self.login('nurse@ipcms.com', 'nurse123')

        # Missing required field (address)
        payload = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@ipcms.com",
            "phone_number": "9876543219",
            "gender": "Female",
            "age": 25
        }
        res = self.client.post('/api/v1/patients', json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("Missing required fields", res.get_json()['message'])

        # Invalid age
        payload['address'] = "123 Green Avenue, Chennai"
        payload['age'] = 200
        res = self.client.post('/api/v1/patients', json=payload)
        self.assertEqual(res.status_code, 400)

        # Invalid gender
        payload['age'] = 25
        payload['gender'] = 'Invalid'
        res = self.client.post('/api/v1/patients', json=payload)
        self.assertEqual(res.status_code, 400)

        # Duplicate email
        payload['gender'] = 'Female'
        payload['email'] = 'patient@ipcms.com' # Seeded patient email
        res = self.client.post('/api/v1/patients', json=payload)
        self.assertEqual(res.status_code, 409)

    def test_03_patient_update_success_and_idor(self):
        """3. Patient can update self, but Patient A cannot update Patient B details."""
        # Patient A (Rahul Kumar, ID 4) updates self
        self.login('patient@ipcms.com', 'patient123')
        payload = {
            "phone_number": "9999999999",
            "address": "Updated Patient 4 Address"
        }
        res = self.client.put('/api/v1/patients/4', json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(db.session.get(Patient, 4).phone_number, '9999999999')

        # IDOR check: Patient A (ID 4) tries to update Patient B
        p_b = User.query.filter_by(email='patient_b@ipcms.com').first()
        res_idor = self.client.put(f'/api/v1/patients/{p_b.id}', json={"phone_number": "0000000000"})
        self.assertEqual(res_idor.status_code, 403)
        self.logout()

    def test_04_patient_delete_by_admin_only(self):
        """4. Admin can delete a patient (soft delete), but Nurse is forbidden."""
        # Nurse try to delete Patient B -> 403
        self.login('nurse@ipcms.com', 'nurse123')
        p_b = User.query.filter_by(email='patient_b@ipcms.com').first()
        res_nurse = self.client.delete(f'/api/v1/patients/{p_b.id}')
        self.assertEqual(res_nurse.status_code, 403)
        self.logout()

        # Admin delete Patient B -> 200
        self.login('admin@ipcms.com', 'admin123')
        res_admin = self.client.delete(f'/api/v1/patients/{p_b.id}')
        self.assertEqual(res_admin.status_code, 200)
        self.assertFalse(db.session.get(User, p_b.id).is_active)
        self.logout()

    # -------------------------------------------------------------------------
    # 2. Appointment CRUD Tests
    # -------------------------------------------------------------------------
    def test_05_appointment_booking_and_conflict(self):
        """5. Book appointment successfully, verify validation & conflict detection."""
        self.login('patient@ipcms.com', 'patient123')
        
        # Valid appointment payload (Dr. John Smith, ID 2)
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        payload = {
            "doctor_id": 2,
            "appointment_date": tomorrow,
            "appointment_time": "11:00 AM" # doctor available 10:00 AM - 01:00 PM
        }
        res = self.client.post('/api/v1/appointments', json=payload)
        self.assertEqual(res.status_code, 201)
        appt_id = res.get_json()['data']['id']

        # Duplicate slot booking (conflict) -> 409
        res_conflict = self.client.post('/api/v1/appointments', json=payload)
        self.assertEqual(res_conflict.status_code, 409)

        # Reschedule/Update slot success -> 200
        payload['appointment_time'] = "12:00 PM"
        res_update = self.client.put(f'/api/v1/appointments/{appt_id}', json=payload)
        self.assertEqual(res_update.status_code, 200)

        # Cancel/Delete appointment success -> 200
        res_delete = self.client.delete(f'/api/v1/appointments/{appt_id}')
        self.assertEqual(res_delete.status_code, 200)
        self.assertEqual(db.session.get(Appointment, appt_id).status, 'Cancelled')

        self.logout()

    # -------------------------------------------------------------------------
    # 3. Consultation Tests
    # -------------------------------------------------------------------------
    def test_06_consultation_creation(self):
        """6. Doctor can create consultation, but Patient/Nurse is forbidden."""
        # Patient forbidden -> 403
        self.login('patient@ipcms.com', 'patient123')
        payload = {
            "patient_id": 4,
            "doctor_id": 2,
            "consultation_date": "2026-08-20",
            "symptoms": "Cough",
            "diagnosis": "Cold",
            "treatment_notes": "Take rest"
        }
        self.assertEqual(self.client.post('/api/v1/consultations', json=payload).status_code, 403)
        self.logout()

        # Doctor success -> 201
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.post('/api/v1/consultations', json=payload)
        self.assertEqual(res.status_code, 201)
        self.logout()

    # -------------------------------------------------------------------------
    # 4. Prescription Tests
    # -------------------------------------------------------------------------
    def test_07_prescription_creation(self):
        """7. Doctor can create prescription with medicine items."""
        self.login('doctor@ipcms.com', 'doctor123')
        payload = {
            "patient_id": 4,
            "prescription_date": "2026-08-20",
            "special_instructions": "Take after meals",
            "items": [
                {"medicine_name": "Paracetamol 500 mg", "dosage": "500mg", "frequency": "Daily", "duration": "3 days"}
            ]
        }
        res = self.client.post('/api/v1/prescriptions', json=payload)
        self.assertEqual(res.status_code, 201)
        self.logout()

    # -------------------------------------------------------------------------
    # 5. Laboratory Tests
    # -------------------------------------------------------------------------
    def test_08_laboratory_report_creation(self):
        """8. Lab Staff can create lab report, Patient is forbidden."""
        # Patient forbidden -> 403
        self.login('patient@ipcms.com', 'patient123')
        payload = {
            "patient_id": 4,
            "doctor_id": 2,
            "test_name": "Thyroid Profile",
            "test_date": "2026-08-20",
            "result": "Normal",
            "remarks": "Thyroid levels stable"
        }
        self.assertEqual(self.client.post('/api/v1/laboratory', json=payload).status_code, 403)
        self.logout()

        # Lab Staff success -> 201
        self.login('labstaff_test@ipcms.com', 'password123')
        res = self.client.post('/api/v1/laboratory', json=payload)
        self.assertEqual(res.status_code, 201)
        self.logout()

    # -------------------------------------------------------------------------
    # 6. Pharmacy/Medicines Tests
    # -------------------------------------------------------------------------
    def test_09_medicine_creation(self):
        """9. Pharmacist can add medicine to inventory, Doctor is forbidden."""
        # Doctor forbidden -> 403
        self.login('doctor@ipcms.com', 'doctor123')
        payload = {
            "medicine_code": "TESTMED999",
            "medicine_name": "Test Medicine 100mg",
            "category": "Tablet",
            "manufacturer": "BioPharma Inc",
            "stock": 100,
            "unit_price": 25.50,
            "expiry_date": "2028-12-31"
        }
        self.assertEqual(self.client.post('/api/v1/pharmacy', json=payload).status_code, 403)
        self.logout()

        # Pharmacist success -> 201
        self.login('pharmacist_test@ipcms.com', 'password123')
        res = self.client.post('/api/v1/pharmacy', json=payload)
        self.assertEqual(res.status_code, 201)

        # Duplicate code -> 409
        res_dup = self.client.post('/api/v1/pharmacy', json=payload)
        self.assertEqual(res_dup.status_code, 409)

        self.logout()

    # -------------------------------------------------------------------------
    # 7. Billing Tests
    # -------------------------------------------------------------------------
    def test_10_billing_creation(self):
        """10. Nurse can generate invoice/bill for a patient."""
        self.login('nurse@ipcms.com', 'nurse123')
        payload = {
            "patient_id": 4,
            "payment_method": "UPI",
            "discount": 50.00,
            "tax_amount": 10.00
        }
        res = self.client.post('/api/v1/billing', json=payload)
        self.assertEqual(res.status_code, 201)
        self.logout()

if __name__ == '__main__':
    unittest.main()
