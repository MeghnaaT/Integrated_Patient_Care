import unittest
import os
import sys
import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.appointment import Appointment
from models.patient import Patient

class TestReports(unittest.TestCase):

    def setUp(self):
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

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

    def test_reports_access_control(self):
        print("\n--- Testing Reports Access Control ---")

        # 1. Anonymous user redirected to login
        res = self.client.get('/reports/', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers['Location'])
        print("OK: Anonymous user redirected.")

        # 2. Patient role gets 403 Forbidden
        self.login('patient@ipcms.com', 'patient123')
        res = self.client.get('/reports/')
        self.assertEqual(res.status_code, 403)
        self.logout()
        print("OK: Patient role forbidden.")

        # 3. Nurse role allowed
        self.login('nurse@ipcms.com', 'nurse123')
        res = self.client.get('/reports/')
        self.assertEqual(res.status_code, 200)
        self.logout()
        print("OK: Nurse role allowed access.")

        # 4. Doctor role allowed
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/reports/')
        self.assertEqual(res.status_code, 200)
        self.logout()
        print("OK: Doctor role allowed access.")

        # 5. Admin role allowed
        self.login('admin@ipcms.com', 'admin123')
        res = self.client.get('/reports/')
        self.assertEqual(res.status_code, 200)
        self.logout()
        print("OK: Admin role allowed access.")

    def test_reports_generation_calculations(self):
        print("\n--- Testing Reports Generation Calculations ---")
        self.login('admin@ipcms.com', 'admin123')

        # Insert a test appointment on a specific date (e.g. July 10, 2026)
        test_date = datetime.date(2026, 7, 10)
        
        # Ensure cleanup first
        Appointment.query.filter_by(patient_id=4, doctor_id=2, appointment_date=test_date).delete()
        db.session.commit()

        new_appt = Appointment(
            patient_id=4,
            doctor_id=2,
            appointment_date=test_date,
            appointment_time=datetime.time(11, 0),
            status='Confirmed'
        )
        db.session.add(new_appt)
        db.session.commit()

        # Query the report page for July 2026
        res = self.client.get('/reports/?report_type=Monthly+Appointment+Report&month=7&year=2026')
        self.assertEqual(res.status_code, 200)
        
        # Check weekly period string exists in output
        self.assertIn(b'08-07-2026 to 14-07-2026', res.data)
        # Check total count is displayed
        self.assertIn(b'Total', res.data)

        # Cleanup
        db.session.delete(new_appt)
        db.session.commit()
        self.logout()
        print("OK: Reports generation output verified successfully.")

if __name__ == '__main__':
    unittest.main()
