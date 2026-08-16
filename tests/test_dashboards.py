import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db

class TestDashboards(unittest.TestCase):

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

    def test_dashboards_data_and_ui(self):
        print("\n--- Testing Dashboards Data and UI ---")

        # 1. Admin Dashboard
        res = self.login('admin@ipcms.com', 'admin123')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Admin Dashboard', res.data)
        self.assertIn(b'Total Patients', res.data)
        self.assertIn(b'Total Doctors', res.data)
        self.assertIn(b'Total Nurses', res.data)
        self.assertIn(b'statusChart', res.data)
        self.assertIn(b'genderChart', res.data)
        self.assertIn(b'Recent Admissions', res.data)
        self.assertIn(b'Recent Bookings', res.data)
        print("OK: Admin Dashboard contains stats, charts, and lists.")
        self.logout()

        # 2. Doctor Dashboard (John Smith is doctor@ipcms.com / doctor123)
        res = self.login('doctor@ipcms.com', 'doctor123')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Doctor Dashboard', res.data)
        self.assertIn(b'Today\'s Consultations', res.data)
        self.assertIn(b'Upcoming Consultations', res.data)
        self.assertIn(b'docStatusChart', res.data)
        self.assertIn(b'Consultation Backlog', res.data)
        self.assertIn(b'Recent EHR Entries', res.data)
        print("OK: Doctor Dashboard contains doctor stats, backlog list, and charts.")
        self.logout()

        # 3. Nurse Dashboard (Sarah Connor is nurse@ipcms.com / nurse123)
        res = self.login('nurse@ipcms.com', 'nurse123')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Nurse Dashboard', res.data)
        self.assertIn(b'Total Active Patients', res.data)
        self.assertIn(b'Today\'s Appointments', res.data)
        self.assertIn(b'nurseStatusChart', res.data)
        self.assertIn(b'Today\'s Appointment Schedule', res.data)
        self.assertIn(b'Active Patients', res.data)
        print("OK: Nurse Dashboard contains active patient list and schedule.")
        self.logout()

        # 4. Patient Dashboard (Ravi Kumar is patient@ipcms.com / patient123)
        res = self.login('patient@ipcms.com', 'patient123')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'My Dashboard', res.data)
        self.assertIn(b'My Consultation Log', res.data)
        self.assertIn(b'patientStatusChart', res.data)
        self.assertIn(b'My Medical History', res.data)
        self.assertIn(b'Book Appointment', res.data)
        self.assertIn(b'Sessions Breakdown', res.data)
        print("OK: Patient Dashboard contains personal agenda, record history, and status charts.")
        self.logout()

if __name__ == '__main__':
    unittest.main()
