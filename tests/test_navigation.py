# =============================================================================
# tests/test_navigation.py — Role-Specific Navigation & Workspace Test Suite
# =============================================================================

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db

class RoleNavigationTestCase(unittest.TestCase):

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

    def test_01_admin_navigation_elements(self):
        """1. Admin receives Admin navigation with administrative tools."""
        self.login('admin@ipcms.com', 'admin123')
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)

        # Admin navigation items present
        self.assertIn(b'href="/system-integration"', res.data)
        self.assertIn(b'href="/testing-performance"', res.data)
        self.assertIn(b'href="/dashboard-overview"', res.data)

        self.logout()

    def test_02_doctor_navigation_elements(self):
        """2. Doctor receives Doctor navigation and Admin tools are absent."""
        self.login('doctor@ipcms.com', 'doctor123')
        res = self.client.get('/doctor/dashboard')
        self.assertEqual(res.status_code, 200)

        # Doctor clinical links present
        self.assertIn(b'My Schedule', res.data)
        self.assertIn(b'My Patients', res.data)
        self.assertIn(b'Consultations', res.data)
        self.assertIn(b'Prescriptions', res.data)

        # Admin-only tools absent from HTML
        self.assertNotIn(b'href="/system-integration"', res.data)
        self.assertNotIn(b'href="/testing-performance"', res.data)

        self.logout()

    def test_03_nurse_navigation_elements(self):
        """3. Nurse receives Nurse navigation and Admin tools are absent."""
        self.login('nurse@ipcms.com', 'nurse123')
        res = self.client.get('/nurse/dashboard')
        self.assertEqual(res.status_code, 200)

        # Nurse clinical links present
        self.assertIn(b'Active Patients', res.data)
        self.assertIn(b'Appointments', res.data)

        # Admin-only tools absent
        self.assertNotIn(b'href="/system-integration"', res.data)
        self.assertNotIn(b'href="/testing-performance"', res.data)

        self.logout()

    def test_04_patient_navigation_elements(self):
        """4. Patient receives Patient self-service portal navigation."""
        self.login('patient@ipcms.com', 'patient123')
        res = self.client.get('/patient/dashboard')
        self.assertEqual(res.status_code, 200)

        # Patient self-service links present
        self.assertIn(b'Book Appointment', res.data)
        self.assertIn(b'Doctors', res.data)
        self.assertIn(b'My EHR', res.data)
        self.assertIn(b'My Prescriptions', res.data)

        # Admin-only tools absent
        self.assertNotIn(b'href="/system-integration"', res.data)
        self.assertNotIn(b'href="/testing-performance"', res.data)

        self.logout()

if __name__ == '__main__':
    unittest.main()
