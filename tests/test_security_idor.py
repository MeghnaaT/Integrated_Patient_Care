# =============================================================================
# tests/test_security_idor.py — Security & IDOR Hardening Test Suite
# =============================================================================

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db

class SecurityIDORHardeningTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('default')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password,
            'remember_me': False
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    def test_01_admin_access_admin_functionality(self):
        """1. Admin can access Admin functionality."""
        self.login('admin@ipcms.com', 'admin123')
        
        res_admin = self.client.get('/admin/dashboard')
        self.assertEqual(res_admin.status_code, 200)

        res_sys = self.client.get('/system-integration')
        self.assertEqual(res_sys.status_code, 200)

        res_perf = self.client.get('/testing-performance')
        self.assertEqual(res_perf.status_code, 200)

        res_analytics = self.client.get('/dashboard-overview')
        self.assertEqual(res_analytics.status_code, 200)

        self.logout()

    def test_02_doctor_own_schedule_access(self):
        """2. Doctor can access own schedule."""
        self.login('doctor@ipcms.com', 'doctor123')
        
        # Logged in doctor has Doctor ID 2
        res_own = self.client.get('/appointment/doctor/2/schedule')
        self.assertEqual(res_own.status_code, 200)

        self.logout()

    def test_03_doctor_cannot_access_another_doctor_schedule(self):
        """3. Doctor cannot access another doctor's schedule (HTTP 403)."""
        self.login('doctor@ipcms.com', 'doctor123')
        
        # Doctor ID 2 attempting to view Doctor ID 5 schedule
        res_other = self.client.get('/appointment/doctor/5/schedule')
        self.assertEqual(res_other.status_code, 403)

        self.logout()

    def test_04_nurse_retains_legitimate_clinical_access(self):
        """4. Nurse retains legitimate clinical access."""
        self.login('nurse@ipcms.com', 'nurse123')
        
        res_nurse_dash = self.client.get('/nurse/dashboard')
        self.assertEqual(res_nurse_dash.status_code, 200)

        res_patients = self.client.get('/patient/list')
        self.assertEqual(res_patients.status_code, 200)

        res_schedule = self.client.get('/appointment/doctor/2/schedule')
        self.assertEqual(res_schedule.status_code, 200)

        self.logout()

    def test_05_patient_can_access_own_ehr(self):
        """5. Patient can access own EHR."""
        self.login('patient@ipcms.com', 'patient123')
        
        # Logged in patient has Patient ID 4
        res_own_ehr = self.client.get('/ehr/4')
        self.assertEqual(res_own_ehr.status_code, 200)

        self.logout()

    def test_06_patient_cannot_access_another_patient_ehr(self):
        """6. Patient cannot access another patient's EHR (HTTP 403)."""
        self.login('patient@ipcms.com', 'patient123')
        
        # Patient ID 4 attempting to view Patient ID 1 EHR
        res_other_ehr = self.client.get('/ehr/1')
        self.assertEqual(res_other_ehr.status_code, 403)

        self.logout()

    def test_07_patient_can_access_own_appointments(self):
        """7. Patient can access own appointments."""
        self.login('patient@ipcms.com', 'patient123')
        
        res_dash = self.client.get('/patient/dashboard')
        self.assertEqual(res_dash.status_code, 200)

        self.logout()

    def test_08_patient_cannot_access_another_patient_appointments_or_invoices(self):
        """8. Patient cannot access another patient's private invoice/data (HTTP 403)."""
        import datetime
        from models.billing import Bill
        from models.patient import Patient

        from services.patient_service import create_patient
        bill_other = Bill.query.filter(Bill.patient_id != 4).first()
        if not bill_other:
            p_other = create_patient({
                'first_name': 'Other', 'last_name': 'Patient',
                'email': f"other_{int(datetime.datetime.now().timestamp())}@ipcms.com",
                'password': 'password123', 'confirm_password': 'password123',
                'phone_number': '9998887779', 'gender': 'Male', 'age': 30, 'blood_group': 'O+', 'address': '123 Main St'
            })
            if p_other:
                bill_other = Bill(patient_id=p_other.id, bill_number=f"BILL_{int(datetime.datetime.now().timestamp())}", sub_total=500.0, total_amount=500.0, payment_status='Paid', bill_date=datetime.date.today(), due_date=datetime.date.today())
                db.session.add(bill_other)
                db.session.commit()

        self.login('patient@ipcms.com', 'patient123')
        
        # Patient ID 4 attempting to view Bill owned by another patient
        res_inv = self.client.get(f"/billing/invoice/{bill_other.id}")
        self.assertEqual(res_inv.status_code, 403)

        self.logout()

    def test_09_unauthorized_roles_cannot_access_admin_tools(self):
        """9. Unauthorized roles cannot access administrative tools (HTTP 403)."""
        # Doctor role attempting admin tools
        self.login('doctor@ipcms.com', 'doctor123')
        self.assertEqual(self.client.get('/system-integration').status_code, 403)
        self.assertEqual(self.client.get('/testing-performance').status_code, 403)
        self.assertEqual(self.client.get('/dashboard-overview').status_code, 403)
        self.logout()

        # Nurse role attempting admin tools
        self.login('nurse@ipcms.com', 'nurse123')
        self.assertEqual(self.client.get('/system-integration').status_code, 403)
        self.assertEqual(self.client.get('/testing-performance').status_code, 403)
        self.assertEqual(self.client.get('/dashboard-overview').status_code, 403)
        self.logout()

        # Patient role attempting admin tools
        self.login('patient@ipcms.com', 'patient123')
        self.assertEqual(self.client.get('/system-integration').status_code, 403)
        self.assertEqual(self.client.get('/testing-performance').status_code, 403)
        self.assertEqual(self.client.get('/dashboard-overview').status_code, 403)
        self.logout()

    def test_10_legitimate_workflows_continue_working(self):
        """10. Existing legitimate workflows continue to work."""
        self.login('admin@ipcms.com', 'admin123')
        res_list = self.client.get('/appointment/list')
        self.assertEqual(res_list.status_code, 200)
        self.logout()

if __name__ == '__main__':
    unittest.main()
