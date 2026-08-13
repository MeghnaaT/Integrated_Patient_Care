# =============================================================================
# tests/test_milestone4_day3.py — Milestone 4 Day 3 Test Suite
# =============================================================================

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from services.workflow_integration_service import execute_complete_patient_workflow

class Milestone4Day3TestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('default')
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

    def test_01_execute_complete_12_step_patient_workflow(self):
        """Test complete 12-step end-to-end patient workflow execution."""
        res = execute_complete_patient_workflow()
        self.assertEqual(res['status'], 'success')
        self.assertIn('patient_name', res)
        self.assertIn('bill_number', res)
        self.assertGreaterEqual(len(res['steps']), 12)

        for step in res['steps']:
            self.assertEqual(step['status'], 'Passed')

    def test_02_system_integration_routes(self):
        """Test /system-integration and /system-integration/run-workflow routes."""
        self.login('admin@ipcms.com', 'admin123')
        
        # Test dashboard page
        res = self.client.get('/system-integration')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'SYSTEM INTEGRATION STATUS', res.data)

        # Test live JSON workflow runner
        res_json = self.client.get('/system-integration/run-workflow')
        self.assertEqual(res_json.status_code, 200)
        json_data = res_json.get_json()
        self.assertEqual(json_data['status'], 'success')

        self.logout()

    def test_03_access_control(self):
        """Test role-based access control on /system-integration."""
        self.login('patient@ipcms.com', 'patient123')
        res = self.client.get('/system-integration')
        self.assertEqual(res.status_code, 403)
        self.logout()

if __name__ == '__main__':
    unittest.main()
