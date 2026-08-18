# =============================================================================
# tests/test_api_security.py — API Security & IDOR Hardening Test Suite
# =============================================================================

import unittest
import os
import sys
import json
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.user import User
from models.role import Role
from models.patient import Patient

class APISecurityTestCase(unittest.TestCase):

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
        # Ensure all roles exist
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

        # Create a second Patient for IDOR testing if not exists
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
        # Clean up test users
        User.query.filter(User.email.in_([
            'pharmacist_test@ipcms.com',
            'labstaff_test@ipcms.com',
            'receptionist_test@ipcms.com',
            'patient_b@ipcms.com'
        ])).delete(synchronize_session=False)
        Patient.query.filter(Patient.email == 'patient_b@ipcms.com').delete(synchronize_session=False)
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

    def test_01_unauthenticated_api_access_rejected(self):
        """1. Unauthenticated users are rejected with HTTP 401 and JSON error."""
        endpoints = [
            '/api/v1/patients',
            '/api/v1/patients/4',
            '/api/v1/doctors',
            '/api/v1/consultations',
            '/api/v1/prescriptions',
            '/api/v1/laboratory',
            '/api/v1/pharmacy',
            '/api/v1/billing',
            '/api/v1/notifications'
        ]
        for url in endpoints:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 401, f"{url} did not return 401")
            json_data = res.get_json()
            self.assertEqual(json_data['success'], False)
            self.assertEqual(json_data['error'], 'Authentication required')

    def test_02_admin_full_api_access(self):
        """2. Admin has complete access to all API endpoints."""
        self.login('admin@ipcms.com', 'admin123')
        endpoints = [
            '/api/v1/patients',
            '/api/v1/patients/4',
            '/api/v1/doctors',
            '/api/v1/consultations',
            '/api/v1/prescriptions',
            '/api/v1/laboratory',
            '/api/v1/pharmacy',
            '/api/v1/billing',
            '/api/v1/notifications'
        ]
        for url in endpoints:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200, f"{url} was rejected for Admin")
        self.logout()

    def test_03_doctor_api_access_scope(self):
        """3. Doctor has access only to clinical endpoints (billing/notifications forbidden)."""
        self.login('doctor@ipcms.com', 'doctor123')
        
        allowed = [
            '/api/v1/patients',
            '/api/v1/patients/4',
            '/api/v1/doctors',
            '/api/v1/consultations',
            '/api/v1/prescriptions',
            '/api/v1/laboratory',
            '/api/v1/pharmacy'
        ]
        for url in allowed:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200, f"{url} was rejected for Doctor")

        forbidden = [
            '/api/v1/billing',
            '/api/v1/notifications'
        ]
        for url in forbidden:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 403, f"{url} was not forbidden for Doctor")
            json_data = res.get_json()
            self.assertEqual(json_data['success'], False)
            self.assertEqual(json_data['error'], 'Insufficient permissions')
        self.logout()

    def test_04_nurse_api_access_scope(self):
        """4. Nurse has access to all clinical/billing/notification endpoints."""
        self.login('nurse@ipcms.com', 'nurse123')
        endpoints = [
            '/api/v1/patients',
            '/api/v1/patients/4',
            '/api/v1/doctors',
            '/api/v1/consultations',
            '/api/v1/prescriptions',
            '/api/v1/laboratory',
            '/api/v1/pharmacy',
            '/api/v1/billing',
            '/api/v1/notifications'
        ]
        for url in endpoints:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200, f"{url} was rejected for Nurse")
        self.logout()

    def test_05_patient_api_access_scope_and_idor(self):
        """5. Patient can only access doctors, self details, and self-owned resources."""
        self.login('patient@ipcms.com', 'patient123')
        
        # Logged in patient is ID 4 (Rahul Kumar)
        self.assertEqual(self.client.get('/api/v1/patients/4').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/doctors').status_code, 200)

        # IDOR prevention: Patient 4 attempting to access Patient B details
        p_b = User.query.filter_by(email='patient_b@ipcms.com').first()
        self.assertIsNotNone(p_b)
        res_idor = self.client.get(f'/api/v1/patients/{p_b.id}')
        self.assertEqual(res_idor.status_code, 403)
        self.assertEqual(res_idor.get_json()['success'], False)
        self.assertEqual(res_idor.get_json()['error'], 'Insufficient permissions')

        # Patients cannot view overall patients directory or pharmacy catalog
        self.assertEqual(self.client.get('/api/v1/patients').status_code, 403)
        self.assertEqual(self.client.get('/api/v1/pharmacy').status_code, 403)

        # Check self-scoped fields return successfully
        self.assertEqual(self.client.get('/api/v1/consultations').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/prescriptions').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/laboratory').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/billing').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/notifications').status_code, 200)

        self.logout()

    def test_06_pharmacist_api_access_scope(self):
        """6. Pharmacist can access only pharmacy info."""
        self.login('pharmacist_test@ipcms.com', 'password123')
        self.assertEqual(self.client.get('/api/v1/pharmacy').status_code, 200)

        forbidden = [
            '/api/v1/patients',
            '/api/v1/patients/4',
            '/api/v1/doctors',
            '/api/v1/consultations',
            '/api/v1/prescriptions',
            '/api/v1/laboratory',
            '/api/v1/billing',
            '/api/v1/notifications'
        ]
        for url in forbidden:
            self.assertEqual(self.client.get(url).status_code, 403, f"{url} should be forbidden for Pharmacist")
        self.logout()

    def test_07_laboratory_staff_api_access_scope(self):
        """7. Laboratory Staff can access only laboratory info."""
        self.login('labstaff_test@ipcms.com', 'password123')
        self.assertEqual(self.client.get('/api/v1/laboratory').status_code, 200)

        forbidden = [
            '/api/v1/patients',
            '/api/v1/patients/4',
            '/api/v1/doctors',
            '/api/v1/consultations',
            '/api/v1/prescriptions',
            '/api/v1/pharmacy',
            '/api/v1/billing',
            '/api/v1/notifications'
        ]
        for url in forbidden:
            self.assertEqual(self.client.get(url).status_code, 403, f"{url} should be forbidden for Laboratory Staff")
        self.logout()

    def test_08_receptionist_api_access_scope(self):
        """8. Receptionist can access only patients and doctors catalog."""
        self.login('receptionist_test@ipcms.com', 'password123')
        self.assertEqual(self.client.get('/api/v1/patients').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/patients/4').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/doctors').status_code, 200)

        forbidden = [
            '/api/v1/consultations',
            '/api/v1/prescriptions',
            '/api/v1/laboratory',
            '/api/v1/pharmacy',
            '/api/v1/billing',
            '/api/v1/notifications'
        ]
        for url in forbidden:
            self.assertEqual(self.client.get(url).status_code, 403, f"{url} should be forbidden for Receptionist")
        self.logout()

if __name__ == '__main__':
    unittest.main()
