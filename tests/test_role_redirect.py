# =============================================================================
# tests/test_role_redirect.py — Post-Login Role Redirection Test Suite
# =============================================================================

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db

class RoleRedirectTestCase(unittest.TestCase):

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

    def test_01_admin_login_redirects_to_admin_dashboard(self):
        """1. Admin login redirects to /admin/dashboard."""
        res = self.client.post('/auth/login', data={
            'email': 'admin@ipcms.com',
            'password': 'admin123'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get('Location'), '/dashboard')

        res_dispatch = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(res_dispatch.status_code, 302)
        self.assertEqual(res_dispatch.headers.get('Location'), '/admin/dashboard')

        res_final = self.client.get('/admin/dashboard')
        self.assertEqual(res_final.status_code, 200)
        self.assertIn(b'Admin Dashboard', res_final.data)

    def test_02_doctor_login_redirects_to_doctor_dashboard(self):
        """2. Doctor login redirects to /doctor/dashboard."""
        res = self.client.post('/auth/login', data={
            'email': 'doctor@ipcms.com',
            'password': 'doctor123'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get('Location'), '/dashboard')

        res_dispatch = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(res_dispatch.status_code, 302)
        self.assertEqual(res_dispatch.headers.get('Location'), '/doctor/dashboard')

        res_final = self.client.get('/doctor/dashboard')
        self.assertEqual(res_final.status_code, 200)
        self.assertIn(b'Doctor Dashboard', res_final.data)

    def test_03_nurse_login_redirects_to_nurse_dashboard(self):
        """3. Nurse login redirects to /nurse/dashboard."""
        res = self.client.post('/auth/login', data={
            'email': 'nurse@ipcms.com',
            'password': 'nurse123'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get('Location'), '/dashboard')

        res_dispatch = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(res_dispatch.status_code, 302)
        self.assertEqual(res_dispatch.headers.get('Location'), '/nurse/dashboard')

        res_final = self.client.get('/nurse/dashboard')
        self.assertEqual(res_final.status_code, 200)
        self.assertIn(b'Nurse Dashboard', res_final.data)

    def test_04_patient_login_redirects_to_patient_dashboard(self):
        """4. Patient login redirects to /patient/dashboard."""
        res = self.client.post('/auth/login', data={
            'email': 'patient@ipcms.com',
            'password': 'patient123'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get('Location'), '/dashboard')

        res_dispatch = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(res_dispatch.status_code, 302)
        self.assertEqual(res_dispatch.headers.get('Location'), '/patient/dashboard')

        res_final = self.client.get('/patient/dashboard')
        self.assertEqual(res_final.status_code, 200)
        self.assertIn(b'My Dashboard', res_final.data)

    def test_05_active_session_relogin_switches_role_correctly(self):
        """5. Logging in as Doctor while Admin session is active logs out Admin and redirects to Doctor dashboard."""
        self.client.post('/auth/login', data={'email': 'admin@ipcms.com', 'password': 'admin123'})
        
        res = self.client.post('/auth/login', data={
            'email': 'doctor@ipcms.com',
            'password': 'doctor123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.request.path, '/doctor/dashboard')
        self.assertIn(b'Doctor Dashboard', res.data)

    def test_06_non_admin_cannot_be_redirected_to_admin_via_next_parameter(self):
        """6. Patient or Doctor with ?next=/admin/dashboard gets safely redirected to own dashboard."""
        res = self.client.post('/auth/login?next=/admin/dashboard', data={
            'email': 'patient@ipcms.com',
            'password': 'patient123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.request.path, '/patient/dashboard')
        self.assertIn(b'My Dashboard', res.data)

if __name__ == '__main__':
    unittest.main()
