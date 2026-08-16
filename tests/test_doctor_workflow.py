# =============================================================================
# tests/test_doctor_workflow.py — Doctor Workflow & Clinical Scope Test Suite
# =============================================================================

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.user import User
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.consultation import Consultation
from models.prescription import Prescription

class DoctorWorkflowTestCase(unittest.TestCase):

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

    def test_01_doctor_dashboard_loads(self):
        """1. Doctor dashboard loads with clinical stats."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/doctor/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Doctor Dashboard', res.data)
        self.logout()

    def test_02_doctor_own_schedule_access(self):
        """2. Doctor can access own schedule."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/appointment/doctor/2/schedule')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Doctor Daily Schedule', res.data)
        self.logout()

    def test_03_doctor_cannot_access_another_doctor_schedule(self):
        """3. Doctor cannot access another Doctor's schedule (HTTP 403)."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/appointment/doctor/999/schedule')
        self.assertEqual(res.status_code, 403)
        self.logout()

    def test_04_doctor_my_patients_scoped(self):
        """4. Doctor's My Patients list is scoped to associated patients only."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/patient/list')
        self.assertEqual(res.status_code, 200)
        # Associated patient (Rahul Kumar, ID 4) present
        self.assertIn(b'Rahul', res.data)
        self.logout()

    def test_05_doctor_search_unrelated_patient_filtered(self):
        """5. Doctor searching for unrelated patient gets 0 results."""
        self.login('doctor@ipcms.com', 'doctor123')
        # Search for a name that belongs to an unassociated patient or non-existent
        res = self.client.get('/patient/list?q=UnrelatedNameXYZ')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b'UnrelatedNameXYZ', res.data)
        self.logout()

    def test_06_doctor_can_open_associated_patient(self):
        """6. Doctor can view associated patient profile."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/patient/view/4')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Rahul Kumar', res.data)
        self.logout()

    def test_07_doctor_cannot_open_unrelated_patient_profile(self):
        """7. Doctor cannot open an unrelated patient's profile (HTTP 403)."""
        self.login('doctor@ipcms.com', 'doctor123')
        # Patient ID 999999 or unassociated
        res = self.client.get('/patient/view/999999')
        self.assertEqual(res.status_code, 403)
        self.logout()

    def test_08_doctor_legitimate_consultation_creation(self):
        """8. Doctor can create a legitimate consultation for an associated patient."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.post('/consultations/add', data={
            'patient_id': 4,
            'doctor_id': 2,
            'consultation_date': '2026-08-14',
            'symptoms': 'Chest pain and shortness of breath',
            'diagnosis': 'Mild angina',
            'treatment_notes': 'Prescribed isosorbide dinitrate and recommended rest'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Consultation Summary', res.data)
        self.logout()

    def test_09_doctor_unauthorized_patient_consultation_rejected(self):
        """9. Doctor cannot create a consultation for an unauthorized patient (HTTP 403)."""
        from services.patient_service import create_patient
        p_unassoc = create_patient({
            'first_name': 'Unassociated', 'last_name': 'Patient9',
            'email': 'unassoc9@ipcms.com', 'phone_number': '1112223339',
            'gender': 'Female', 'age': 40, 'blood_group': 'A+',
            'address': '999 Test Street, Test City, TC 99999'
        })
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.post('/consultations/add', data={
            'patient_id': p_unassoc.id,
            'doctor_id': 2,
            'consultation_date': '2026-08-14',
            'symptoms': 'Malicious attempt',
            'diagnosis': 'None',
            'treatment_notes': 'None'
        })
        self.assertEqual(res.status_code, 403)
        self.logout()

    def test_10_doctor_legitimate_prescription_creation(self):
        """10. Doctor can create a prescription for an associated patient."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.post('/prescriptions/add', data={
            'patient_id': 4,
            'doctor_id': 2,
            'prescription_date': '2026-08-14',
            'special_instructions': 'Take after meals',
            'medicine_name_1': 'Aspirin 75mg',
            'dosage_1': '1 tablet',
            'frequency_1': 'Once Daily',
            'duration_1': '30 Days'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Prescription #', res.data)
        self.logout()

    def test_11_doctor_unauthorized_patient_prescription_rejected(self):
        """11. Doctor cannot create a prescription for an unauthorized patient (HTTP 403)."""
        from services.patient_service import create_patient
        p_unassoc = create_patient({
            'first_name': 'Unassociated', 'last_name': 'Patient11',
            'email': 'unassoc11@ipcms.com', 'phone_number': '1112223331',
            'gender': 'Female', 'age': 40, 'blood_group': 'A+',
            'address': '111 Test Avenue, Test City, TC 11111'
        })
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.post('/prescriptions/add', data={
            'patient_id': p_unassoc.id,
            'doctor_id': 2,
            'prescription_date': '2026-08-14',
            'special_instructions': 'Malicious prescription',
            'medicine_name_1': 'Restricted drug',
            'dosage_1': '100mg',
            'frequency_1': 'Daily',
            'duration_1': '5 Days'
        })
        self.assertEqual(res.status_code, 403)
        self.logout()

    def test_12_doctor_clinical_reports_allowed(self):
        """12. Doctor can view clinical reports (patient, appointment, consultation, prescription)."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/reports/admin?report_type=patient')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Patient Report', res.data)
        self.logout()

    def test_13_doctor_admin_financial_reports_prohibited(self):
        """13. Doctor cannot access Admin financial/billing reports (HTTP 403)."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/reports/admin?report_type=billing')
        self.assertEqual(res.status_code, 403)
        self.logout()

    def test_14_doctor_admin_system_tools_prohibited(self):
        """14. Doctor cannot access Admin system tools (HTTP 403)."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/system-integration')
        self.assertEqual(res.status_code, 403)
        res2 = self.client.get('/testing-performance')
        self.assertEqual(res2.status_code, 403)
        res3 = self.client.get('/dashboard-overview')
        self.assertEqual(res3.status_code, 403)
        self.logout()

    def test_15_doctor_feedback_scoped(self):
        """15. Doctor feedback dashboard loads scoped for doctor."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/feedback/admin')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Patient Feedback', res.data)
        self.logout()

if __name__ == '__main__':
    unittest.main()
